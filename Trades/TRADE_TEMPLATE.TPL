{
  "trade": {
    "id": "71717f7d-b848-4a35-9bea-33427e8e4110",
    "asset": "ICN",
    "symbol": "ICNBTC",
    "side": "SELL",
    "status": "COMPLETED",
    "entry": {
      "side": "BUY",
      "smart": true,
      "threshold": "0.00000020",
      "targets": [
        {
          "status": "COMPLETED",
          "price": "0.00014421",
          "vol": "3800.00000000"
        }
      ]
    },
    "exit": {
      "side": "SELL",
      "smart": false,
      "threshold": "0.30%",
      "targets": [
        {
          "status": "COMPLETED",
          "id": 9672903,
          "date": "2018-04-20 02:21:48",
          "price": "0.00015601",
          "vol": "25%",
          "smart": true,
          "best_price": "0.00015529"
        },
        {
          "status": "COMPLETED",
          "id": 9871297,
          "date": "2018-04-21 18:28:12",
          "price": "0.00017600",
          "vol": "33%",
          "sl": "0.00015000"
        },
        {
          "price": "0.00018700",
          "vol": "50%"
        },
        {
          "price": "0.00020800",
          "vol": "100%",
          "smart": true
        }
      ]
    },
    "stoploss": {
      "type": "FIXED",
      "last_stoploss": "0.00015000",
      "initial_target": {
        "status": "COMPLETED",
        "id": 10166677,
        "date": "2018-04-25 13:25:20",
        "price": "0.00013144",
        "vol": "100%"
      }
    }
  }
}