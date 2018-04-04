{
    "trades": [
        {
            "entry": {
                "target": {
                    "price": "0.00129000",
                    "vol": "20"
                },
                "sl_threshold": "0.00000120",
                "pullback_threshold": "0.00001800",
                "side": "BUY"
            },

            "side": "SELL",
            "symbol": "LSKBTC",
            "asset": "LSK",

            "sl_settings": {
                "type": "TRAILING",
                "val": "10.00%",
                "limit_price_threshold": "0.10%",
                "threshold": 0.0002,

                "initial_target": {
                    "price": "0.00110000",
                    "vol": "100.00%"
                }
            },


            "targets": [
                {
                    "price": "0.00133000",
                    "vol": "10",
                    "sl": "0.00125000",
                },
                {
                    "price": "0.00144000",
                    "vol": "100.00%"
                }
            ],
            "status": "NEW"
        }
    ]
}