from datetime import datetime

from Bot.OrderEnums import OrderStatus
from Bot.Value import Value


class Target:
    def __init__(self, price, vol, status=OrderStatus.NEW.value, date=None, id=None, sl=0):
        self.date = date
        self.id = id
        self.status = OrderStatus(status.lower())
        self.vol = Value(vol)
        self.price = PriceHelper.parse_price(price)
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
        if PriceHelper.is_float_price(self.price):
            return '{}:{:.08f}@{}'.format('StopLoss' if self.is_stoploss_target() else 'Regular', self.price, self.vol)
        else:
            return '{}:{}@{}'.format('StopLoss' if self.is_stoploss_target() else 'Regular', self.price, self.vol)

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

        if PriceHelper.is_float_price(self.price):
            d['price'] = fmt.format(self.price)
        else:
            d['price'] = self.price

        d['vol'] = self.vol

        return d


class PriceHelper:
    CURR_PRICE_TOKEN = 'cp'

    def __init__(self, is_digit, price_val, operand, operation_val):
        self.is_digit = is_digit
        self.price_val = price_val
        self.operand = operand
        self.operation_val: Value = operation_val

    def get_value(self, ref_price):
        if self.is_digit:
            return self.price_val

        if str(self.price_val).lower() == 'cp':
            if not self.operand:
                return ref_price
            if self.operand in ['+', '-']:
                return round(ref_price + self.operation_val.get_val(ref_price) * (1 if self.operand == '+' else -1), 8)
            else:
                raise SyntaxError('Operation "{}" is unsupported. Use only + or -'.format(self.operand))

        raise SyntaxError('Reference price "{}" is unsupported. Use only "CP"'.format(str(self.price_val)))


    @classmethod
    def parse_price(cls, price_str):
        try:
            return float(price_str)
        except ValueError:
            return price_str

    @classmethod
    def is_float_price(cls, price_str):
        try:
            float(price_str)
            return True
        except ValueError:
            return False

    @classmethod
    def create_price_helper(cls, price_str):

        s = str(price_str).strip().lower()
        if PriceHelper.is_float_price(s):
            return PriceHelper(True, float(s), None, None)

        token = s
        operand = None
        val = None
        if s.startswith(PriceHelper.CURR_PRICE_TOKEN):
            token = PriceHelper.CURR_PRICE_TOKEN

            s = s[len(PriceHelper.CURR_PRICE_TOKEN):]
            if len(s) > 0 and s[0] in ['+', '-']:
                operand = s[0]
                s = s[1:]
                if len(s) > 0:
                    val = Value(s)

        return PriceHelper(False, token, operand, val)


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
