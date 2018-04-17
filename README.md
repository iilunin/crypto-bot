# Cryptobot

The main purpose of the bot is to keep track of your Binance trades while you're away. 
This bot is not supposed to earn money by itself, it requires targets and stop-loss inputs.

This project is based on [sammchardy/python-binance](https://github.com/sammchardy/python-binance) 
Binance API wrapper
  
## Features
- Manage an unlimited number of trading pairs
- Supports smart trade entry, though I often buy coins myself. 
- Unlimited exit targets and smart last target (will be possible to have more smart targets soon)
- Flexible stop loss settings: Fixed/Trialing + Custom SL after each target reached.
- OCO 
- FREE :)

## Limitations
- Can't have multiple trades of for one trading pair

## Installation
[Setup Instructions](./Docs/SETUP.md)

## Flow
[Flow Description](./Docs/FLOW.md)

## Trade File
[Trade File Description](./Docs/TRADE_FILE.md)