# Cryptobot Flow

The bot doesn't place any orders intentionally except of ones specified in [trade files](./TRADE_FILE.md).

## Work with trade files
Bot automatically monitors `Active` trades folder for any changes like added, updated or removed trade files.
1. If the new file is detected and it is a valid trade file:
    - The bot will adjust its name (if needed to match `{SYMBOL}_{guid}.json` pattern e.g. `ADABTC_29868502-ef0e-42a8-91fe-76dc08879bae.json`)
    - Load this trade to the trade list and start executing it
2. If the existing file was modified (changed stop-losses, targets, etc.):
    - Reload this file and validate it
    - Update existing trade - likely to cancel all existing limit ond stop-loss orders, 
    and put new ones if guided by trade
3. If trade file was deleted:
    - Remove the trade from the execution list. 
    - All placed orders **will not** be canceled

## Execute trades
The bot connects to Binance WebSocket API to get real-time symbol tickers and get user data notifications
such as balance change, order creation or cancellation. It also uses REST API to get additional information
about exchange rules and limits and other functionality like placing orders.

In general, the trade flow comprised of up to 3 execution strategies:
1. Entry
2. Exit
3. Stop Loss

Each strategy is optional. Each strategy has a target which is essentially price and volume and additional configuration
parameters.

Trade strategies are checked/executed each 500ms if there were bid/ask price changes during that period.

_"Smart Target"_ - is a target with the trailing stop-loss or take profit approach. If you sell at a price `100` and have a smart target
with `threshold` `1%` it means that once the price reaches `100` stop-loss sell order will be placed at `99`. If the price goes up, 
the order updates (cancels and places the new one) for the better price (for the price `105` stop-loss order will be `103.95`).
It works in both directions - buy or sell whether it is Entry, Exit or Stop Loss strategy.

Right now "Smart" approach is tested only with stop-loss orders as it guarantees in case of spike your order will be triggered
and executed immediately by the exchange. But this approach exhaust APIs as it makes at least 2 API calls to update the order 
(cancel and place new). Market Orders approach is being tested, but it may end you up with a worst price.

Each Trade may or may not have set `cap` parameter to limit trades against the whole available balance.

### Entry
Entry strategy is active if the trade has `entry` section and trade `status` is `NEW`. Currently, it supports only smart entry.
Once the entry is completed, bot sets the trade's `status` to `ACTIVE` and the `cap` of the trade equal to the entry volume. 
e.g., if you bought 100 ltc, but have another 500 in your wallet the whole trade will be capped by 100 ltc. If trade doesn't 
have `exit` section, then it is marked as completed and no more actions on assets will be performed within this trade.

### Exit
Exit strategy is active if the trade has `exit` section and trade `status` is `ACTIVE` and has at least one not completed target.
Exit can have multiple limit and smart targets. If the Stop Loss strategy is also active, then Exit strategy works concurrently
with Stop Loss providing One Cancels Other functionality. Exit strategy creates limit orders for all regular targets and 
executes "Smart" approach for all smart targets. If all targets are completed, then the trade is marked as completed and 
no more actions on assets will be performed within this trade.

### Stop Loss
Stop Loss strategy is active if the trade has `stoploss` section and trade `status` is `ACTIVE`. Stop Loss has two modes `FIXED` and
`TRAILING`. With `FIXED` mode initial target stop-loss settings will be used by default. In `TRAILING` mode initial target stop
loss settings used by default, and actual trailing is enabled after the first target completed. Both these modes can be overridden 
by specific `sl` set in the particular `exit` target. 

For instance, you have initial `FIXED` stop-loss set to 100, and exit target #3 has `sl` set to 220. In this scenario stop-loss 100
will be active until exit target #3 is hit, and after that stop-loss will become 220.

Another example, if you have initial `TRAILING` stop-loss set to 100 and 5% trailing value, and exit target #3 has `sl` set to 220.
In this scenario 100 will be active stop-loss until the first exit target is completed, after that trailing mode kicks in,
and stop-loss automatically adjusted to 5% of the price. When exit target #3 is completed stop-loss becomes fixed to 220.
Once the next exit target without overridden stoploss is completed, trailing mode kicks in again.

**One Cancels Other** works this way. If price falls (or jumps in case of buy order) closer to active stop-loss value - 
within `zone_entry` which is `0.3%` by default, then Stop Loss strategy takes control over. In this case all orders placed by 
Exit strategy are canceled, and stop-loss order is placed instead. If the price goes back to normal and leaves this zone,
then control is given back to Exit strategy. If price hits stop-loss order and it's executed, then the trade is marked as completed.
Sometimes price falls significantly between the decision to place stop-loss order and actually placing it, so that the price is 
lower that the stop-loss order. In this case, Market order will be placed immediately.
 
 