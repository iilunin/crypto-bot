from datetime import datetime

from Bot.OrderStatus import OrderStatus
from Bot.Value import Value


class Target:
    def __init__(self, price, vol, status=OrderStatus.NEW.value, date=None, id=None, sl=0):
        self.date = date
        self.id = id
        self.status = OrderStatus(status.lower())
        self.vol = Value(vol)
        self.price = float(price)
        self.sl = float(sl)

    def is_completed(self):
        return self.status == OrderStatus.COMPLETED

    def is_new(self):
        return self.status == OrderStatus.NEW

    def is_active(self):
        return self.status == OrderStatus.ACTIVE

    def has_id(self):
        return self.id is not None

    # def set_completed(self, date_str=datetime.now().replace(microsecond=0).isoformat(' ')):
    def set_completed(self, date=datetime.now()):
        self.status = OrderStatus.COMPLETED
        self.date = date

    def set_canceled(self):
        self.status = OrderStatus.NEW
        self.id = None

    def set_active(self, id):
        self.status = OrderStatus.ACTIVE
        self.id = id

    def has_custom_stop(self):
        return self.sl != 0

    def custom_stop(self):
        return self.sl

    def is_stoploss_target(self):
        return False

    def is_regular_target(self):
        return False

    def is_entry_target(self):
        return False

    def __str__(self):
        return '{}:{:.08f}@{}'.format('StopLoss' if self.is_stoploss_target() else 'Regular', self.price, self.vol)

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

    def is_regular_target(self):
        return True

class StopLossTarget(Target):
    def __init__(self, params):
        super().__init__(**params)

    def is_stoploss_target(self):
        return True


class EntryTarget(Target):
    def __init__(self, params):
        super().__init__(**params)

    def is_entry_target(self):
        return True
