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
        self.init_smart_exit()
        if self.assign_calculated_volume(self.trade_targets()):
            self.trade_updated(self.trade, True)

    def get_trade_section(self):
        return self.trade.exit # can be interface for entry at some point too

    def has_smart_target(self):
        return len(self.get_trade_section().get_all_incomplete_smart_targets()) > 0

    def init_smart_exit(self):
        if self.has_smart_target():
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

            # execute strategy for smart orders
            if self.strategy_exit:
                self.strategy_exit.execute(new_price)

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

        self.strategy_exit = None
        self.init_smart_exit()

        if self.assign_calculated_volume(self.trade_targets()):
            self.trade_updated(self.trade, True)

    def trade_targets(self):
        return self.trade.exit.targets

    def not_completed_targets(self):
        return [t for t in self.trade_targets() if not t.is_completed()]

    def validate_all_orders(self, targets):
        return all(t.status.is_completed() or (t.status.is_active() and t.has_id()) for t in targets if not t.is_smart())

    def validate_all_completed(self, targets):
        return all(t.status.is_completed() for t in targets)

    def prepare_volume_allocation(self, targets):
        currency_balance = self.get_balance_for_side()

        bal = self.trade.get_cap(currency_balance.avail) + (
            currency_balance.locked if any(t.is_active() for t in targets) else 0)

        if bal <= 0:
            self.logWarning('Available balance is 0')
            return

        orders = []
        # last_target = targets[-1] if self.last_target_smart() else None

        for t in targets:
            if t.is_completed():
                continue

            price = self.exchange_info.adjust_price(t.price)

            adjusted_balance = bal

            # in case of BUY like with BTCUSDT we have balance in USDT e.g. 700, but specifying the vol in BTC e.g. 0.1
            if self.trade_side().is_buy():
                adjusted_balance = round(bal / price, 8)

            vol = self.exchange_info.adjust_quanity(t.vol.get_val(adjusted_balance))
            t.calculated_volume = vol

            if vol == 0:
                self.logWarning('No volume left to process order @ price {:.0f}'.format(price))
                continue

            if bal - vol < 0:
                self.logWarning(
                    'Insufficient balance to place order. Bal: {}, Order: {}. Target: {}'.format(bal, vol, t.__str__()))
                return

            # place only new and not smart targets
            if t.is_new() and not t.is_smart():
                # if self.last_target_smart() and t == last_target:
                #     continue
                orders.append({
                    'price': self.exchange_info.adjust_price(price),
                    'volume': vol,
                    'side': self.trade_side().name,
                    'target': t})

            if self.trade_side().is_sell():
                bal = round(bal - vol, 8)
            else:
                bal = round(bal - t.vol.get_val(bal), 8)

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





