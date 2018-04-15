from binance.exceptions import BinanceAPIException

from Bot.Strategy.EntryStrategy import ExitStrategy
from Bot.TradeEnums import OrderStatus
from Bot.FXConnector import FXConnector
from Bot.Strategy.TradingStrategy import TradingStrategy
from Bot.Trade import Trade
from Bot.Value import Value


class PlaceOrderStrategy(TradingStrategy):
    def __init__(self, trade: Trade, fx: FXConnector, trade_updated=None, nested=False, exchange_info=None, balance=None):
        super().__init__(trade, fx, trade_updated, nested, exchange_info, balance)
        self.strategy_exit = None
        # self.init_smart_exit()

    def last_target_smart(self):
        return self.trade.exit.last_target_smart

    def init_smart_exit(self):
        if self.last_target_smart():
            self.strategy_exit = ExitStrategy(self.trade, self.fx, self.trade_updated, True, self.exchange_info,
                                              self.balance)

    def execute(self, new_price):
        try:
            if self.is_completed():
                return

            targets = self.trade_targets()

            if self.validate_all_completed(targets):
                self.logInfo('All Orders are Completed')
                self.set_trade_completed()
                return

            if self.last_target_smart():
                not_completed_targets = self.not_completed_targets()
                if len(not_completed_targets) == 1:

                    if not self.strategy_exit: # LAZY LOAD
                        self.init_smart_exit()

                    self.strategy_exit.execute(new_price)
                    return

            if self.validate_all_orders(targets):
                return

            alloc = self.prepare_volume_allocation(targets)

            if alloc:
                self.place_orders(alloc)
                self.logInfo('All Orders are Placed')
        except BinanceAPIException as bae:
            self.logError(str(bae))

    def update_trade(self, trade: Trade):
        self.trade = trade

        if self.trade.exit.last_target_smart:
            self.init_smart_exit()
        else:
            self.strategy_exit = None

    def trade_targets(self):
        return self.trade.exit.targets

    def not_completed_targets(self):
        return [t for t in self.trade_targets() if not t.is_completed()]

    def validate_all_orders(self, targets):
        if self.last_target_smart():
            if len(targets) > 1:
                targets = targets[:-1]
        return all(t.status.is_completed() or (t.status.is_active() and t.has_id()) for t in targets)

    def validate_all_completed(self, targets):
        return all(t.status.is_completed() for t in targets)

    def prepare_volume_allocation(self, targets):
        bal = self.balance.avail + (self.balance.locked if any(t.is_active() for t in targets) else 0)

        if bal <= 0:
            self.logWarning('Available balance is 0')
            return

        orders = []
        last_target = targets[-1] if self.last_target_smart() else None

        for t in targets:
            if t.is_completed():
                continue

            price = self.exchange_info.adjust_price(t.price)

            vol = self.exchange_info.adjust_quanity(t.vol.get_val(bal))

            if vol == 0:
                self.logWarning('No volume left to process order @ price {:.0f}'.format(price))
                continue

            if bal - vol < 0:
                self.logWarning('Insufficient balance to place order. Bal: {}, Order: {}'.format(bal, vol))
                return

            if t.is_new() and t != last_target:
                orders.append({
                    'price': self.exchange_info.adjust_price(price),
                    'volume': self.exchange_info.adjust_quanity(vol),
                    'side': self.trade_side().name,
                    'target': t})

            bal -= vol

        self.logInfo('Orders to be posted: {}'.format(orders))
        return orders

    def place_orders(self, allocations):
        for a in allocations:
            target = a.pop('target', None)
            order = self.fx.create_limit_order(sym=self.symbol(), **a)
            target.set_active(order['orderId'])
        self.trigger_target_updated()

    def on_order_status_changed(self, t, data):
        if not t.is_exit_target():
            return

        if t.is_completed():
            self.logInfo('Target {} completed'.format(t))
        else:
            self.logInfo('Order status updated: {}'.format(t.status))





