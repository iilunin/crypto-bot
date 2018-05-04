{
  "trade": {
    "asset": "ADA",
    "symbol": "ADABTC",
    "side": "SELL",
    "status": "NEW",
    "entry": {
      "targets": [
        {
          "price": "0.00002950",
          "vol": "1300"
        }
      ]
    },
    "exit": {
      "threshold": "0.50%",
      "targets": [
        {
          "price": "0.00003250",
          "vol": "20%"
        },
        {
          "price": "0.00003400",
          "vol": "33%"
        },
        {
          "price": "0.00003600",
          "vol": "50%"
        },
        {
          "vol": "100%",
          "price": "0.00004100",
          "smart": true
        }
      ]
    },
    "stoploss": {
      "type": "FIXED",
      "initial_target": {
        "price": "0.00002500",
        "vol": "100%"
      }
    }
  }
}