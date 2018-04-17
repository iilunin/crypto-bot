# Cryptobot Setup Instructions

# Mac

Docker time issue.
API configuration

```
docker pull iilunin/crypto-bot

docker run -d --rm --name cryptobot \
-e "TZ=America/New_York" \
-e "KEY=BINANCE_API_KEY" \
-e "SECRET=BINANCE_API_SECRET" \
-v $(pwd)/Trades/Portfolio:/usr/src/trades \
-v $(pwd)/Trades/Completed:/usr/src/complete_trades \
-v $(pwd)/Conf:/usr/src/configs:ro \
iilunin/crypto-bot
```