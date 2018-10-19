# Cryptobot

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
