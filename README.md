# simple_discord_bot

A Discord bot that can perform various tasks such as telling jokes, replying to keywords, helping admins with moderation, checking bot latency, creating polls, tracking user levels, checking cryptocurrency prices, and notifying users about mining pool events.

## Features
Discord bot that can:
* tell jokes
* reply when it detects keyword in message
* help admins with moderation by deleting given number of messages
* check bot latency
* create simple yes/no poll
* keep track of user level on the server
* check price of a coin via coinmarketcap api
* check for latest block on mining pool
* check for latest payout from mining pool
* notify user about new payout from mining pool
* notify user about new block on mining pool
* notify user about offline worker on mining pool

## Commands

The bot supports the following commands:

- `!joke`: Tells a random joke.
- `!ping`: Checks the bot latency.
- `!poll <question>`: Creates a simple yes/no poll with reactions.
- `!level`: Shows your current level on the server.
- `!price <coin>`: Checks the price of a cryptocurrency from CoinMarketCap (requires COINMARKETCAP_KEY).
- `!block`: Checks the latest block on the mining pool.
- `!payout`: Checks the latest payout from the mining pool.
- `!help`: Shows a list of available commands.
- `!add_watch_wallet <wallet_address>`: add wallet to watch list to get notifications (one wallet per user)
- `!remove_watch_wallet`: remove wallet from watch list and stop getting notifications

## Setup:
1. Clone this repository to your local machine.
2. Create a Discord application and a bot account from the [Discord Developer Portal](https://discord.com/developers/applications).
3. Create a file named `.env` in the root directory and add the following variables (use .example.env as template):
   - `TOKEN`: Your bot token from the [Discord Developer Portal](https://discord.com/developers/applications).
   - `ZETPOOL_CHANNEL_ID`: Channel ID from your discord server that mining pool notifications will be displayed on.
   - `CMC_API_KEY`: Your API key from [CoinMarketCap](https://pro.coinmarketcap.com/account).
4. Create new virtual env:
``` sh
python -m venv env
```
5. Activate your virtual env:
``` sh
env/Scripts/activate
```
6. Install packages from included requirements.txt:
``` sh
pip install -r .\requirements.txt
```

## Usage:
1. Start the bot:
``` sh
python .\main.py
```


### Screenshots

Here are some screenshots of the bot in action:

![Bot telling a joke](https://github.com/dawmro/simple_discord_bot/blob/main/screenshot1.PNG?raw=true)

![Help menu](https://github.com/dawmro/simple_discord_bot/blob/main/screenshot2.PNG?raw=true)

![Block notification](https://github.com/dawmro/simple_discord_bot/blob/main/screenshot_new_block.PNG?raw=true)
