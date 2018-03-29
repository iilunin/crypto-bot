import json

from Bot.OrderStatus import OrderStatus


class Target:
    def __init__(self, price, vol, status=OrderStatus.NEW.value, date=None, id=None, sl=0):
        self.date = date
        self.id = id
        self.status = OrderStatus(status.lower())
        self.vol = vol
        self.price = float(price)
        self.sl = float(sl)

    def is_completed(self):
        return self.status == OrderStatus.COMPLETED

    def has_id(self):
        return self.id is not None

    def set_completed(self):
        self.status = OrderStatus.COMPLETED

    def has_custom_stop(self):
        return self.sl != 0

    def custom_stop(self):
        return self.sl

    def is_stoploss_target(self):
        return None

    def __str__(self):
        return '{}:{}@{}'.format('SL' if self.is_stoploss_target() else 'REG', self.price, self.vol)

    def to_json_dict(self):
        fmt = '{:.8f}'
        d = {}

        if self.date:
            d['date'] = self.date

        if self.id:
            d['id'] = self.id

        if self.sl != 0:
            d['sl'] = fmt.format(self.sl)

        if self.status != OrderStatus.NEW:
            d['status'] = self.status

        d['price'] = fmt.format(self.price)
        d['vol'] = self.vol

        return d


class RegularTarget(Target):
    def __init__(self, params):
        super().__init__(**params)

    def is_stoploss_target(self):
        return False


class StopLossTarget(Target):
    def __init__(self, params):
        super().__init__(**params)

    def is_stoploss_target(self):
        return True
