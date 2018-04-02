from Bot.Value import Value


class SmartOrder:
    def __init__(self, sym, is_buy, price, buy_ignore_threshold=False, sl_threshold=Value("0.04%"), pull_back=Value("1.6%")):
        self.sym = sym
        self.is_buy = is_buy
        self.target_price = price
        self.last_best_price = 0
        self.allow_buy_after_threshold = buy_ignore_threshold

        self.sl_threshold = sl_threshold
        self.pull_back_threshold = pull_back

        self.target_zone_touched = False
        self.bought = False

        self.init_settings()

    def init_settings(self):
        if self.sl_threshold.is_abs():
            self.sl_threshold_val = self.sl_threshold.v
        else:
            self.sl_threshold_val = round(self.target_price * (self.sl_threshold.v / 100), 8)

        if self.pull_back_threshold.type == Value.Type.ABS:
            self.pull_back_threshold_val = self.pull_back_threshold.v
        else:
            self.pull_back_threshold_val = round(self.target_price * (self.pull_back_threshold.v / 100), 8)

        self.sl_threshold_zone_limit = round(self.target_price + self.sl_threshold_val * (1 if self.is_buy else -1), 8)

        print('{} Pulback: {:.8f}; Limit: {:.8f}'.format(self.sym, self.pull_back_threshold_val, self.sl_threshold_zone_limit))

    def price_update(self, new_price):
        if self.bought:
            return

        target_zone = ((self.is_buy and new_price <= self.target_price) or (
                    not self.is_buy and new_price >= self.target_price))

        if target_zone:
            self.target_zone_touched = True

        if not self.allow_buy_after_threshold:
            # consider this zone only if we touched target zone
            if self.target_zone_touched:
                sl_treshhold_zone = ((self.is_buy and new_price <= self.sl_threshold_zone_limit) or (
                            not self.is_buy and new_price >= self.sl_threshold_zone_limit))
            else:
                sl_treshhold_zone = False

            self.target_zone_touched = sl_treshhold_zone

        if self.target_zone_touched:
            if self.last_best_price == 0:
                self.last_best_price = new_price

            # work with pull-back and stoploss

            pb_limit = self.last_best_price + self.pull_back_threshold_val * (1 if self.is_buy else -1)
            fn = min if self.is_buy else max
            pb_limit = fn(pb_limit, self.sl_threshold_zone_limit)

            print('{} will be triggered when price will reach {}; Current price: {}'.format(
                'Buy' if self.is_buy else 'Sell', pb_limit, new_price))

            if ((self.is_buy and new_price >= pb_limit) or
                    (not self.is_buy and new_price <= pb_limit)):
                self.trigger_buy(new_price)
                return True

            if ((self.is_buy and self.last_best_price > new_price) or
                    (not self.is_buy and self.last_best_price < new_price)):
                self.last_best_price = new_price
        else:
            self.target_zone_touched = target_zone

        return False

    def trigger_buy(self, price):
        self.bought = True
        print('{} {}, {:.08f}'.format('Buy' if self.is_buy else 'Sell', self.sym, price))



