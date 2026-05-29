import asyncio, logging, time, sys
from os import getenv
from datetime import datetime

from dotenv import load_dotenv

import aiohttp
from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.filters import Command
from aiogram.types import Message, BotCommand, TelegramObject


logging.getLogger('aiogram.event').setLevel(logging.WARNING) 
logger = logging.getLogger('session')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))


load_dotenv()


TOKEN = getenv('TG_TOKEN')
log_file_path = getenv('LOG_FILE')
ip = getenv('IP')
server_url = f'http://{ip}/'


html_help_message = (
    '<b>Command list</b>:\n'
    '<i>/start</i> default start message\n'
    "<i>/help</i> u read it now, don't u?\n"
    '<i>/state</i> current crawl state\n'
    '<i>/crawl_start</i> start web search robot\n'
    '<i>/crawl_stop</i> stop web search robot\n'
    '<i>/crawl_add</i> <b>[<i>url1</i> <i>url2</i> ... <i>url50</i>]</b> add urls to crawl queue\n'
    '<i>/search</i> <b>[<i>search request</i>]</b> add urls to crawl queue\n'
)


dp = Dispatcher()


async def on_startup():
    session = aiohttp.ClientSession()
    dp['http_session'] = session


async def on_shutdown():
    await dp['http_session'].close()


class LogMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        user = data.get('event_from_user')
        start = time.time()
        result = await handler(event, data)
        logger.info(f'{datetime.now()} user_id: {user.id if user else "?"} type: {type(event).__name__} handled in {time.time() - start:.3f}s')
        return result


dp.message.middleware(LogMiddleware())
dp.startup.register(on_startup)
dp.shutdown.register(on_shutdown)


@dp.message(Command('start'))
async def command_start_handler(message: Message) -> None:
    await message.answer('Hi, this is a client for [web search engine](https://github.com/box1bs/wfts)', parse_mode='MarkdownV2')


@dp.message(Command('help'))
async def command_start_handler(message: Message) -> None:
    await message.answer(html_help_message, parse_mode='HTML')


@dp.message(Command('state'))
async def command_state_handler(message: Message, http_session: aiohttp.ClientSession) -> None:
    try:
        async with http_session.get(url=server_url+'crawl/state', timeout=aiohttp.ClientTimeout(total=3)) as resp:
            if resp.status != 200:
                raise Exception(f'invalid status code: {resp.status}')
            data = await resp.json()
            await message.answer(f'Last start: {data['LastStart']}\nUptime: {data['Uptime']}\nIndexed: {data['DocsInIndex']}\nRunning state: {'running' if data['IsRunning'] else 'stopped'}\n')
    except (aiohttp.ServerTimeoutError, asyncio.TimeoutError):
        await message.answer('Timeout')

    except aiohttp.ClientResponseError as e:
        await message.answer(f'Response error: {e}')

    except aiohttp.ClientError as e:
        await message.answer(f'Error on server side: {e}')

    except Exception as e:
        await message.answer(f'Unexpected error: {type(e).__name__} {e}')


@dp.message(Command('crawl_start'))
async def command_crawl_start_handler(message: Message, http_session: aiohttp.ClientSession) -> None:
    try:
        async with http_session.post(url=server_url+'crawl/start', timeout=aiohttp.ClientTimeout(total=3)) as resp:
            if resp.status != 201:
                raise Exception(f'invalid status code: {resp.status}')
            await message.answer('Successfully started')
    except (aiohttp.ServerTimeoutError, asyncio.TimeoutError):
        await message.answer('Timeout')

    except aiohttp.ClientResponseError as e:
        await message.answer(f'Response error: {e}')

    except aiohttp.ClientError as e:
        await message.answer(f'Error on server side: {e}')

    except Exception as e:
        await message.answer(f'Unexpected error: {type(e).__name__} {e}')


@dp.message(Command('crawl_stop'))
async def command_crawl_stop_handler(message: Message, http_session: aiohttp.ClientSession) -> None:
    try:
        async with http_session.post(url=server_url+'crawl/stop', timeout=aiohttp.ClientTimeout(total=3)) as resp:
            if resp.status != 200:
                raise Exception(f'invalid status code: {resp.status}')
            await message.answer('Successfully stopped')
    except (aiohttp.ServerTimeoutError, asyncio.TimeoutError):
        await message.answer('Timeout')

    except aiohttp.ClientResponseError as e:
        await message.answer(f'Response error: {e}')

    except aiohttp.ClientError as e:
        await message.answer(f'Error on server side: {e}')

    except Exception as e:
        await message.answer(f'Unexpected error: {type(e).__name__} {e}')


@dp.message(Command('crawl_add'))
async def command_add_urls_handler(message: Message, http_session: aiohttp.ClientSession) -> None:
    urls = message.text.removeprefix('/crawl/add').strip().split()
    query_len = len(urls)
    if query_len == 0:
        await message.answer('empty urls list')
        return

    if query_len > 50:
        urls = urls[:50]

    try:
        async with http_session.patch(url=server_url+'crawl/add', json={'urls': urls}, timeout=aiohttp.ClientTimeout(total=3)) as resp:
            if resp.status != 202:
                raise Exception(f'invalid status code: {resp.status}')
            await message.answer('Successfully added')
    except (aiohttp.ServerTimeoutError, asyncio.TimeoutError):
        await message.answer('Timeout')

    except aiohttp.ClientResponseError as e:
        await message.answer(f'Response error: {e}')

    except aiohttp.ClientError as e:
        await message.answer(f'Error on server side: {e}')

    except Exception as e:
        await message.answer(f'Unexpected error: {type(e).__name__} {e}')


@dp.message(Command('search'))
async def command_search_handler(message: Message, http_session: aiohttp.ClientSession) -> None:
    query = message.text.removeprefix('/search').strip()
    if len(query) == 0:
        await message.answer('empty query')
        return
    
    try:
        async with http_session.get(url=server_url+'search', params={'query': '%20'.join(query.split()), 'cap': 10}, timeout=aiohttp.ClientTimeout(total=3)) as resp:
            if resp.status != 200:
                raise Exception(f'invalid status code: {resp.status}')
            data = await resp.json()
            docs, rels, metrics = data['Docs'], data['Rels'], data['Metrics']
            ans_mess = ['<b>Search Results</b>:']
            for i, (doc, rel) in enumerate(zip(docs, rels), 1):
                ans_mess.append(f'<b>{i}.</b> {doc['url']}')
                ans_mess.append(f'<i>tf_idf</i>: {rel['Tf_Idf']},\n<i>BM25</i>: {rel['BM25']}')

            metrics_str = (
                f'\n<b>Handling time:</b>\n'
                f'• Query: {metrics["HandleQuery"]}\n'
                f'• Fetching: {metrics["FetchAndProcess"]}\n'
                f'• Sorting: {metrics["Sort"]}\n'
                f'• Total: {metrics["Total"]}\n'
                f'• Total results count: {metrics["TotalResults"]}'
            )
            ans_mess.append(metrics_str)
            await message.answer('\n'.join(ans_mess), parse_mode='HTML')

    except (aiohttp.ServerTimeoutError, asyncio.TimeoutError):
        await message.answer('Timeout')

    except aiohttp.ClientResponseError as e:
        await message.answer(f'Response error: {e}')

    except aiohttp.ClientError as e:
        await message.answer(f'Error on server side: {e}')

    except Exception as e:
        await message.answer(f'Unexpected error: {type(e).__name__} {e}')


async def set_main_menu(bot: Bot):
    commands = [
        BotCommand(command='start', description='default start message'),
        BotCommand(command='help', description='command list with descriptions'),
        BotCommand(command='state', description="get crawl's current state"),
        BotCommand(command='crawl_start', description='start remote crowling'),
        BotCommand(command='crawl_stop', description='stop remote crowling'),
        BotCommand(command='crawl_add', description='add urls to crawl queue'),
        BotCommand(command='search', description='search in current indexed space'),
    ]
    await bot.set_my_commands(commands=commands)
    

async def main() -> None:
    bot = Bot(token=TOKEN)
    await set_main_menu(bot)
    await dp.start_polling(bot)
    

if __name__ == "__main__":
    asyncio.run(main())