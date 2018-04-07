{
    "trades": [
        {
            "side": "SELL",
            "entry": {
                "sl_threshold": "0.00000010",
                "pullback_threshold": "0.00000010",
                "side": "BUY",
                "type": "SMART",
                "targets": [
                    {
                        "price": "0.00000518",
                        "vol": "3800"
                    }
                ]
            },
            "exit": {
                "side": "SELL",
                "type": "TARGET",
                "targets": [
                    {
                        "price": "0.00000595",
                        "vol": "25.00%",
                        "sl": "0.00000528"
                    },
                    {
                        "status":"COMPLETED",
                        "price": "0.00000609",
                        "vol": "25.00%"
                    },
                    {
                        "price": "0.00000647",
                        "vol": "50.00%"
                    },
                    {
                        "price": "0.00000718",
                        "vol": "100.00%"
                    }
                ]
            },
            "symbol": "TRXBTC",
            "sl_settings": {
                "type": "FIXED",
                "val": "5.00%",
                "limit_price_threshold": "0.10%",
                "threshold": "0.3%",
                "initial_target": {
                    "price": "0.00000469",
                    "vol": "100.00%"
                }
            },
            "asset": "TRX",
            "status": "COMPLETED"
        }
    ]
}