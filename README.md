# Setup the bot
You will need to install docker

```
docker pull iilunin/crypto-bot

docker run -d --rm --privileged --name cryptobot \
-e "TZ=America/New_York" \
-e "KEY=BINANCE_API_KEY" \
-e "SECRET=BINANCE_API_SECRET" \
-v $(pwd)/Trades/Portfolio:/usr/src/trades \
-v $(pwd)/Trades/Completed:/usr/src/complete_trades \
-v /etc/localtime:/etc/localtime:ro \
iilunin/crypto-bot
```