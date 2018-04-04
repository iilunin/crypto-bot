from Bot.Value import Value


class SmartOrder:
    def __init__(self, is_buy, price, on_update=None, sl_threshold=Value("0.08%"), pull_back=Value("0.6%")):
        self.is_buy = is_buy
        self.target_price = price
        self.best_pullback_limit_price = 0

        self.sl_threshold_val = sl_threshold.get_val(self.target_price)
        self.pull_back_threshold_val = pull_back.get_val(self.target_price)
        self.sl_threshold_zone_limit = round(self.target_price + self.sl_threshold_val * (1 if self.is_buy else -1), 8)

        self.target_zone_touched = False
        self.on_update = on_update
        print('Target Price: {:.8f}; Max Pullback Trigger: {:.8f}; Allowed Limit: {:.8f}'.format(self.target_price,  self.pull_back_threshold_val, self.sl_threshold_zone_limit))


    def price_update(self, price):
        if self.within_target_zone(price):
            self.target_zone_touched = True

        # went out of threshold zone
        if not self.within_threshold_zone(price):
            self.target_zone_touched = False
            self.best_pullback_limit_price = 0

        if self.target_zone_touched:
            # work with pull-back and stoploss
            limit_for_this_price = price + self.pull_back_threshold_val * (1 if self.is_buy else -1)

            minormax = min if self.is_buy else max
            limit_for_this_price = minormax(limit_for_this_price, self.sl_threshold_zone_limit)

            if self.best_pullback_limit_price != 0:
                limit_for_this_price = minormax(limit_for_this_price, self.best_pullback_limit_price)

            limit_for_this_price = round(limit_for_this_price, 8)
            # print('{} will be triggered when price will reach {}; Current price: {}'.format(
            #     'Buy' if self.is_buy else 'Sell', limit_for_this_price, price))

            # if pullback limit changed
            if ((self.is_buy and self.best_pullback_limit_price > limit_for_this_price) or
                    (not self.is_buy and self.best_pullback_limit_price < limit_for_this_price) or
                    self.best_pullback_limit_price == 0):
                self.best_pullback_limit_price = limit_for_this_price
                print('pullback')
                self.trigger_buy(self.best_pullback_limit_price)

            # if price approaches limit
            elif (((self.is_buy and price >= limit_for_this_price) or
                  (not self.is_buy and price <= limit_for_this_price)) and
                  self.best_pullback_limit_price != limit_for_this_price):
                print('limit')
                self.trigger_buy(self.best_pullback_limit_price)

    def within_target_zone(self, price):
        return (self.is_buy and price <= self.target_price) or (
                not self.is_buy and price >= self.target_price)

    def within_threshold_zone(self, price):
        return ((self.is_buy and price <= self.sl_threshold_zone_limit) or
                (not self.is_buy and price >= self.sl_threshold_zone_limit))

    def get_last_pullback_limit(self):
        return self.best_pullback_limit_price

    def trigger_buy(self, pb_limit):
        print('Setting StopLoss-{} for {:.08f}'.format('Buy' if self.is_buy else 'Sell', pb_limit))
        if self.on_update:
            self.on_update(pb_limit)



