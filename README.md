## Minimalistic telegram client for [wfts](https://github.com/box1bs/wfts)
[![BOT](https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/wfts) [![Server](https://img.shields.io/badge/GitHub-Repository-black?style=for-the-badge&logo=github)](https://github.com/box1bs/wfts)

## Command overview
### /help
Shows the command list with description to each one
![help command](assets/help.png)

### /state
Shows current crawl state from [wfts](https://github.com/box1bs/wfts) server.
![state command](assets/state.png)
Access to less info then using the api directly.

### /crawl_start
Start indexing on the remote server.

### /crawl_stop
Stop indexing on the remote server.

### /crawl_add (awaits for a list of <50 urls)
Add some non-empty list of valid urls.

### /search (some string)
Return list of relevant sites with relevance metrics.
![search results](assets/search.png)