# Cryptobot
[![Build Status](https://dev.azure.com/iluninigor/CryptoBot/_apis/build/status/BuildImage?branchName=develop)](https://dev.azure.com/iluninigor/CryptoBot/_build/latest?definitionId=3&branchName=develop)

The main purpose of the bot is to keep track of your Binance trades while you're away. 
This bot is not supposed to earn money by itself, it requires targets and stop-loss inputs to follow your trades.

Binance REST API is based on [sammchardy/python-binance](https://github.com/sammchardy/python-binance) project

**Please read carefully all provided documentation before using the bot** 

## Disclaimer
- **Use it at your own risk.**
- It is not a commercial project, immediate response and or fixes are not guaranteed.
- This project was developed to improve my personal experience with Binance trading,
I am not taking any responsibility for the outcomes you get when using it.  
- Works on Mac and Amazon Linux. Other platforms were not verified.

## Donations
![](./Docs/uf.png )

All donations will go to support people of Ukraine suffering from Russian invasion 
- BTC - 357a3So9CbsNfBBgFYACGvxxS6tMaDoa1P
- ETH and USDT (ERC-20) - 0x165CD37b4C644C2921454429E7F9358d18A45e14
- $DOT: 1x8aa2N2Ar9SQweJv9vsuZn3WYDHu7gMQu1RePjZuBe33Hv.

## Features
- Simple Web User Interface 
- Manage an unlimited number of trading pairs
- Supports "smart" trade entry 
- Unlimited exit targets 
- Each exit target can be "smart" to gain max profits
- Flexible stop loss settings: Fixed/Trialing + Custom SL after each target reached
- One Cancels the Other functionality (OCO) 
- FREE :)

Edit View: ![Edit View](./Docs/edit_view.png "Edit View")

## Limitations
- Can't have multiple trades for one trading pair
- If you place orders manually, there is a chance they will be canceled by bot

## Installation
[Setup Instructions](./Docs/SETUP.md)

## Flow
[Flow Description](./Docs/FLOW.md)

## Trade File
[Trade File Description](./Docs/TRADE_FILE.md)

[Trade File Examples](./Docs/TRADE_FILE_EXAMPLES.md)

## Management API (Coming soon)
[API](./Docs/API.md)

## Channels
[Telegram Discussion Channel](https://t.me/CryptoTradingBotDiscussion)

[Telegram Announcement Channel](https://t.me/OpenSourceCryptoTradingBot)