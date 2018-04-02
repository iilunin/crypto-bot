from Bot.Value import Value


class SmartOrder:
    def __init__(self, sym, is_buy, price, buy_ignore_threshold=False,
                 on_update=None, sl_threshold=Value("0.08%"), pull_back=Value("0.6%")):
        self.sym = sym
        self.is_buy = is_buy
        self.target_price = price
        self.best_pb_limit = 0
        self.allow_buy_after_threshold = buy_ignore_threshold

        self.sl_threshold = sl_threshold
        self.pull_back_threshold = pull_back

        self.target_zone_touched = False
        self.bought = False
        self.on_update = on_update

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

        print('{}. Target Price: {:.8f}; Max Pulback: {:.8f}; Limit: {:.8f}'.format(self.sym, self.target_price,  self.pull_back_threshold_val, self.sl_threshold_zone_limit))

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
            # work with pull-back and stoploss

            limit_for_this_price = new_price + self.pull_back_threshold_val * (1 if self.is_buy else -1)

            fn = min if self.is_buy else max
            limit_for_this_price = fn(limit_for_this_price, self.sl_threshold_zone_limit)

            if self.best_pb_limit != 0:
                limit_for_this_price = fn(limit_for_this_price, self.best_pb_limit)

            print('{} will be triggered when price will reach {}; Current price: {}'.format(
                'Buy' if self.is_buy else 'Sell', limit_for_this_price, new_price))

            if ((self.is_buy and new_price >= limit_for_this_price) or
                    (not self.is_buy and new_price <= limit_for_this_price)):
                self.trigger_buy(new_price, limit_for_this_price)
                return True

            if ((self.is_buy and self.best_pb_limit > limit_for_this_price) or
                    (not self.is_buy and self.best_pb_limit < new_price) or
                    self.best_pb_limit == 0):
                self.best_pb_limit = limit_for_this_price
                self.trigger_buy(new_price, limit_for_this_price)
        else:
            self.target_zone_touched = target_zone

        return False

    def trigger_buy(self, current_price, pb_limit):
        print('{} {}, {:.08f}'.format('Buy' if self.is_buy else 'Sell', self.sym, current_price))
        if self.on_update:
            self.on_update(pb_limit)


