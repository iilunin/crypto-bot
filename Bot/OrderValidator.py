from Bot.Trade import Trade
from Bot.OrderEnums import OrderStatus, Side


class OrderValidator:

    def __init__(self):
        self.errors = {}
        self.warnings = {}

    def validate(self, order):
        """

        :type order: Trade
        """

        self.errors = {}
        self.warnings = {}

        self.validate_completed(order)
        self.validate_sl(order)

        if len(self.errors) > 0:
            return False

        return True


    def validate_completed(self, order):
        if order.is_completed():
            self.errors["ORDER_COMPLETED"] = 'order already completed and should not be executed'


    def validate_sl(self, order):
        """

        :type order: Trade
        """

        if not order.has_stoploss():
            if not order.has_entry(): #in case it is entry only order
                self.errors["NO_SL"] = 'no stop loss set'
            return False

        if order.get_initial_stop().is_completed():
            self.errors["NO_SL"] = 'no active stop loss set'
            return False

        if not order.has_targets():
            self.warnings["NO_TARG"] = 'no targets set'

        for t in order.targets:
            if t.status == OrderStatus.COMPLETED:
                continue

            if (order.side == Side.SELL and order.get_initial_stop().price >= t.price) or \
                    (order.side == Side.BUY and order.get_initial_stop().price <= t.price):
                self.errors['SL_PRICE_ERROR'] = 'stop loss price > than target price'
                return False

        return True
