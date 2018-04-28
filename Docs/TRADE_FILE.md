# Trade File Structure
Trade file is a simple JSON document describing different trade parameters and used by bot to store some additional trading
states. 

Here is the example of the new trade document

```json
{
  "trade": {
    "id": "71717f7d-b848-4a35-9bea-33427e8e4110",
    "asset": "ICN",
    "symbol": "ICNBTC",
    "side": "SELL",
    "status": "NEW",
    "entry": {
      "side": "BUY",
      "smart": true,
      "threshold": "0.00000020",
      "targets": [
        {
          "price": "0.00014421",
          "vol": "4000"
        }
      ]
    },
    "exit": {
      "side": "SELL",
      "smart": false,
      "threshold": "0.30%",
      "targets": [
        {
          "price": "0.00015601",
          "vol": "25%",
          "smart": true
        },
        {
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
      "initial_target": {
        "price": "0.00013144",
        "vol": "100%"
      }
    }
  }
}
```

## trade

It is the parent section where all configuration is stored

|Parameter|Required|Description|
|---|---|---|
|`id`|N|When you create a new trade `id` should be deleted, otherwise it may interfere with existing trade. Bot automatialy generates id for new trades|
|`asset`|Y| Base asset you want to buy or sell|
|`symbol`|Y| The name of the market in Binance|
|`side`|Y| `BUY` or `SELL`|
|`status`|Y| Can be `NEW`, `ACTIVE` or `COMPLETED`. Set `NEW` if you want to process an `entry`, otherwise set `ACTIVE`|
|`cap`|N| Absolute cap value of the coins this trade can use. It will be overridden only by actual coins bought when `entry` is completed.|
|**`entry`**|N| Describes entry parameters and target|
|**`exit`**|N| Describes entry parameters and targets|
|**`stoploss`**|N| Describes stop-loss parameters and targets|

## entry
This section is optional and can be deleted is no automatic entry is needed. 
It supports only one target and only trailing approach at this time. 

|Parameter|Required|Description|
|---|---|---|
|`side`|N|If not specified will use side opposite to `trade.side`.|
|`smart`|N|Ignore. Entry is only "smart".|
|`threshold`|N| Order will be executed if the price falls below the threshold of the best price. Can be absolute or relative value. Default value: `1%`. See [flow documentation](./FLOW.md) "Smart Target" description to get a better idea.|
|`targets`|Y| Section where targets are described. Supports only one target. Supports only `price` and `vol` attributes for the target.|

## exit
This section is optional and can be deleted is no automatic exit is needed. 
It supports limit and "smart" - take profit targets.  

|Parameter|Required|Description|
|---|---|---|
|`side`|N|If not specified will use the same side as `trade.side`.|
|`smart`|N| `true` or `false`. Defines default behavior for `targets` section. Can be overridden by each particular target. Default: `false`|
|`threshold`|N| Order will be executed if the price falls below the threshold of the best price. Can be absolute or relative value. Default value: `1%`. See [flow documentation](./FLOW.md) "Smart Target" description to get a better idea.|
|`targets`|Y| Section where targets are described.|

## stoploss
This section is optional and can be deleted is no automatic exit is needed. 
It supports limit and "smart" - take profit targets.  

|Parameter|Required|Description|
|---|---|---|
|`type`|N|`FIXED` or `TRAILING`, Default: `FIXED`|
|`threshold`|N| Order will be executed if the price falls below the threshold of the best price. Can be absolute or relative value. Default value: `5%`. See [flow documentation](./FLOW.md) "Smart Target" description to get a better idea.|
|`zone_entry`|N| Provides a range to activate stop-limit order beforehand. Can be absolute or relative to the current stop-loss price. Exit from the stop-loss activation zone is double this value. Default: `0.3%`|
|`limit_price_threshold`|N| Provides the limit for stop-limit price (you always specify stop and limit in Binance). Can be absolute or relative to the current stop-loss price.Default: `0.3%`|
|`initial_target`|Y| Initial target for the stop-loss.|

## target
Describes price, volume and other target parameters
|Parameter|Required|Description|
|---|---|---|
|`price`|Y| The price you want to buy or sell this target|
|`vol`|N| If not set defaulted to `100%`. Can be absolute or relative number of remaining coins.|
|`sl`|N| If set, then stoploss strategy will use its value when this target is completed. See more info in the [flow documentation](./FLOW.md).|
|`smart`|N| `true` or `false`. Overrides `smart` attribute of the `exit` section. If true uses `threshold` value of the `exit` section. Default: `false`|


# Examples of volume allocations

## Example 1
In this case there will be the next coin allocation, assuming there are 4000 available coins:
1. Smart Target. Price: `0.00015601`. Allocated 0.25*4000 = `1000`. Volume Left: 3000. Trailing stop loss order will be placed only when reached the price.
2. Limit target. Price: `0.00017600`. Allocated 0.33*3000 = ~`1000`. Volume Left 2000. Limit Order placed immediately.
3. Limit target. Price: `0.00018700`. Allocated 0.5 *2000 = ~`1000`. Volume Left 1000. Limit Order placed immediately.
4. Smart Target. Price: `0.00020800`. Allocated 1.00*1000 = ~`1000`. Volume Left 0. Trailing stop loss order will be placed only when reached the price.

```json
{
  "trade": {
    "asset": "ICN",
    "symbol": "ICNBTC",
    "side": "SELL",
    "status": "NEW",
    "exit": {
      "targets": [
        {
          "price": "0.00015601",
          "vol": "25%",
          "smart": true
        },
        {
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
    }
  }
}
```

## Example 2
In this case there will be the next coin allocation, assuming there are 4000 available coins:
2. Limit target. Price: `0.00017600`. Allocated `2000`. Volume Left 2000. Limit Order placed immediately.
3. Limit target. Price: `0.00018700`. Allocated 0.5 *2000 = ~`1400`. Volume Left 600. Limit Order placed immediately.
4. Smart Target. Price: `0.00020800`. Allocated 1.00*1000 = ~`600`. Volume Left 0. Trailing stop loss order will be placed only when reached the price.

```json
{
  "trade": {
    "asset": "ICN",
    "symbol": "ICNBTC",
    "side": "SELL",
    "status": "NEW",
    "exit": {
      "targets": [
        {
          "price": "0.00017600",
          "vol": "2000",
          "sl": "0.00015000"
        },
        {
          "price": "0.00018700",
          "vol": "70%"
        },
        {
          "price": "0.00020800",
          "vol": "100%",
          "smart": true
        }
      ]
    }
  }
}
```