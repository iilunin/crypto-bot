# Trade File Examples

Make sure to read [trade files structure](./TRADE_FILE.md)

## Example 1 BTC-USDT
Example of the trade to gradually buy BTC. `limit_price_threshold` is set to `0.5%` as prices are more volatile. 
The lowest price order `8300` will be trailing profits with `threshold` `0.2%`. Which means if BTC price falls to `8200`, 
and then pulls back `0.2%` (~8,216.4) the order executes. 

```json
{
  "trade": {
    "asset": "BTC",
    "symbol": "BTCUSDT",
    "side": "BUY",
    "status": "ACTIVE",
    "exit": {
      "threshold": "0.20%",
      "targets": [
        {
          "price": "8800",
          "vol": "25%"
        },
        {
          "price": "8600",
          "vol": "33%"
        },
        {
          "price": "8400",
          "vol": "50%"
        },
        {
          "price": "8300",
          "vol": "100%",
          "smart": true
        }
      ]
    },
    "stoploss": {
      "type": "FIXED",
      "limit_price_threshold": "0.50%",
      "initial_target": {
        "price": "9600",
        "vol": "100%"
      }
    }
  }
}
```

## Example 2 TRX-BTC Trailing
This trade has trailing stop loss and trailing profits last order. The execution flow is the following:
1. There is no default stop loss. Trailing stop loss (00000650) will be activated only after at least one exit target is executed. 
2. If target one hits (00000850), then it marked as completed, and it triggers trailing stop loss. It immediately raises
stop slos to 799 (6% of current price 850) and continue follows the price tightening stop loss.
3. If target 2 hit, it cancels trailing stop loss, and sets it to the fixed value 00000900.
4. If target 3 hit, it triggers back trailing stop loss and raises it to 00001023.
5. If target 4 hit, it activates trailing profits with a small threshold 0.4%.
6. The trade will be completed on a price pull back by triggered trailing profits stop limit order, as its threshold is less
than stop loss threshold.

```json
{
  "trade": {
    "asset": "TRX",
    "symbol": "TRXBTC",
    "side": "SELL",
    "status": "ACTIVE",
    "exit": {
      "threshold": "0.40%",
      "targets": [
        {
          "price": "0.00000850",
          "vol": "25%"
        },
        {
          "price": "0.00001018",
          "vol": "33%",
          "sl": "0.00000900"
        },
        {
          "price": "0.00001088",
          "vol": "50%"
        },
        {
          "price": "0.00001140",
          "vol": "100%",
          "smart": true
        }
      ]
    },
    "stoploss": {
      "type": "TRAILING",
      "threshold": "6%",
      "initial_target": {
        "price": "0.00000650",
        "vol": "100%"
      }
    }
  }
}
```
