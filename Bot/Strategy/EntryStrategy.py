from binance.exceptions import BinanceAPIException

from Bot.OrderStatus import OrderStatus
from Bot.FXConnector import FXConnector
from Bot.Strategy.SmartOrder import SmartOrder
from Bot.Strategy.TradingStrategy import TradingStrategy
from Bot.Target import Target
from Bot.Trade import Trade
from Bot.Value import Value


class EntryStrategy(TradingStrategy):
    def __init__(self, trade: Trade, fx: FXConnector, trade_updated=None, nested=False, exchange_info=None, balance=None):
        super().__init__(trade, fx, trade_updated, nested, exchange_info, balance)
        self.smart_order = SmartOrder(self.symbol(), self.side() == Trade.Side.BUY, self.trade_target().price, True)

    def execute(self, new_price):
        try:
            if self.is_completed():
                return

            target = self.trade_target()

            if self.validate_all_completed([target]):
                self.logInfo('All Orders are Completed')
                self.set_trade_completed()
                return

            if self.validate_all_orders([target]):
                return

            if self.smart_order.price_update(new_price):
                self.place_orders(
                    [{'price': self.exchange_info.adjust_price(new_price),
                    'volume': self.exchange_info.adjust_quanity(target.vol.v),
                    'side': self.side().name,
                    'target': target}])

                self.logInfo('Entry Order is Placed')
        except BinanceAPIException as bae:
            self.logError(str(bae))

    def side(self):
        return Trade.Side.BUY if self.trade.side == Trade.Side.SELL else Trade.Side.SELL

    def trade_target(self):
        return self.trade.entry.target

    def validate_all_orders(self, targets):
        return all(t.status == OrderStatus.ACTIVE or t.has_id() for t in targets)

    def validate_all_completed(self, targets):
        return all(t.status == OrderStatus.COMPLETED for t in targets)

    def prepare_volume_allocation(self, targets):
        bal = self.balance.avail + (self.balance.locked if any(t.is_active() for t in targets) else 0)

        if bal <= 0:
            self.logWarning('Available balance is 0')
            return

        orders = []
        for t in targets:
            price = self.exchange_info.adjust_price(t.price)

            if t.vol.type == Value.Type.ABS:
                vol = self.exchange_info.adjust_quanity(t.vol.v)
            else:
                vol = self.exchange_info.adjust_quanity(bal * (t.vol.v / 100))

            if vol == 0:
                self.logWarning('No volume left to process order @ price {:.0f}'.format(price))
                continue

            if bal - vol < 0:
                self.logWarning('Insufficient balance to place order. Bal: {}, Order: {}'.format(bal, vol))
                return

            if t.is_new():
                orders.append({
                    'price': self.exchange_info.adjust_price(price),
                    'volume': self.exchange_info.adjust_quanity(vol),
                    'side': self.side().name,
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

    def order_status_changed(self, t: Target, data):
        if not t.is_entry_target():
            return

        if t.is_completed():
            self.logInfo('Target {} completed'.format(t))
        else:
            self.logInfo('Order status updated: {}'.format(t.status))





