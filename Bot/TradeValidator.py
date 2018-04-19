from Bot.Trade import Trade
from Bot.TradeEnums import OrderStatus, Side


class TradeValidator:

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


    def validate_sl(self, trade):
        """

        :type trade: Trade
        """

        if not trade.has_stoploss():
            if not trade.has_entry(): #in case it is entry only order
                self.warnings["NO_SL"] = 'no stop loss set'
        elif trade.get_initial_stop().is_completed():
            self.warnings["NO_SL"] = 'no active stop loss set'


        if not (trade.has_exit() or trade.has_entry()):
            self.warnings["NO_TARG"] = 'no targets set'

            for t in trade.exit.targets:
                if t.is_completed() or t.is_smart():
                    continue

                if (trade.side.is_sell() and trade.get_initial_stop().price >= t.price) or \
                        (trade.side.is_buy() and trade.get_initial_stop().price <= t.price):
                    self.errors['SL_PRICE_ERROR'] = 'stop loss price > than target price'
                    return False

        return True
