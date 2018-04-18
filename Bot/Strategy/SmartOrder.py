from Bot.Value import Value
from Utils.Logger import Logger


class SmartOrder(Logger):
    def __init__(self, is_buy, price, sl_threshold=Value("1%"), logger: Logger = None,
                 best_price=0):

        super().__init__(logger)
        self.is_buy = is_buy
        self.target_price = None
        self.initialized = False

        self.sl_threshold = sl_threshold

        self.best_pullback_limit_price = best_price
        self.target_zone_touched = False if self.best_pullback_limit_price == 0 else True

        self.init_price(price)

    def init_price(self, price):
        if not price or isinstance(price, str):
            return

        if not self.is_init():
            self.target_price = price
            self.initialized = True

        sl_limit = self.get_sl_and_pb(price)
        self.logInfo('Target Price: {:.8f}; With Stop Loss Threshold: {:.8f}'.format(self.target_price, sl_limit))

    def get_sl_and_pb(self, price):
        return self.get_price_limit(price, self.sl_threshold)

    def get_price_limit(self, price, val):
        return round(price + val.get_val(price) * (1 if self.is_buy else -1), 8)

    def is_init(self):
        return self.initialized

    def price_update(self, price):
        if not self.initialized:
            return None

        if self.within_target_zone(price):
            self.target_zone_touched = True

        sl_limit = self.get_sl_and_pb(price)

        if self.target_zone_touched:
            minormax = min if self.is_buy else max

            if self.best_pullback_limit_price != 0:
                sl_limit = minormax(sl_limit, self.best_pullback_limit_price)

            self.best_pullback_limit_price = round(sl_limit, 8)

        return self.best_pullback_limit_price

    def within_target_zone(self, price):
        return (self.is_buy and price <= self.target_price) or (
                not self.is_buy and price >= self.target_price)
