from Bot.OrderStatus import OrderStatus
from Bot.FXConnector import FXConnector
from Bot.Strategy.TradingStrategy import TradingStrategy
from Bot.Trade import Trade
from Bot.Value import Value


class PlaceOrderStrategy(TradingStrategy):
    def __init__(self, trade: Trade, fx: FXConnector, trade_updated=None, nested=False, exchange_info=None, balance=None):
        super().__init__(trade, fx, trade_updated, nested, exchange_info, balance)
        self.validate_asset_balance()

    def execute(self, new_price):
        if self.is_completed():
            return

        targets = self.trade_targets()

        if self.validate_all_compoleted(targets):
            self.logInfo('All Orders are Completed')
            self.set_trade_completed()
            return

        if self.validate_all_orders(targets):
            return

        alloc = self.prepare_volume_allocation(targets)

        if alloc:
            self.place_orders(alloc)
            self.logInfo('All Orders are Placed')

    def side(self):
        return self.trade.side

    def trade_targets(self):
        return self.trade.get_available_targets()

    def validate_all_orders(self, targets):
        return all(t.status == OrderStatus.ACTIVE or t.has_id() for t in targets)

    def validate_all_compoleted(self, targets):
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
            target.id = order['orderId']
            target.status = OrderStatus.ACTIVE

        self.trigger_target_updated()





