from collections import OrderedDict
from datetime import datetime

from Bot.CustomSerializable import CustomSerializable
from Bot.TradeEnums import OrderStatus
from Bot.Value import Value


class Target(CustomSerializable):
    def __init__(self, price, vol='100%', **kvargs):
        self.vol = Value(vol)
        self.price = PriceHelper.parse_price(price)

        self.id = kvargs.get('id')
        self.date = kvargs.get('date')
        self.status = OrderStatus(kvargs.get('status', OrderStatus.NEW.name).lower())
        self.sl = float(kvargs.get('sl', 0))
        self.smart = self.s2b(kvargs.get('smart', None))
        self.parent_smart = kvargs.get('parent_smart', None)
        self.best_price = float(kvargs.get('best_price', 0))

        cv = kvargs.get('calculated_volume', None)
        self.calculated_volume = float(cv) if cv else None

    def s2b(self, s):
        if isinstance(s, bool):
            return s
        if s is None:
            return None
        if s.lower() in ['true', 'yes']:
            return True
        return False


    def is_completed(self):
        return self.status.is_completed()

    def is_new(self):
        return self.status.is_new()

    def is_active(self):
        return self.status.is_active()

    def has_id(self):
        return self.id is not None

    # def set_completed(self, date_str=datetime.now().replace(microsecond=0).isoformat(' ')):
    def set_completed(self, id=None, date=datetime.now()):
        self.status = OrderStatus.COMPLETED
        self.date = date
        if id:
            self.id = id

    def set_canceled(self):
        self.status = OrderStatus.NEW
        self.id = None

    def set_active(self, id=None):
        self.status = OrderStatus.ACTIVE
        if id:
            self.id = id

    def has_custom_stop(self):
        return self.sl != 0

    def custom_stop(self):
        return self.sl

    def is_stoploss_target(self):
        return False

    def is_exit_target(self):
        return False

    def is_entry_target(self):
        return False

    def is_smart(self):
        if self.parent_smart is not None:
            if self.smart is not None:
                return self.smart
            return self.parent_smart

        return False if self.smart is None else self.smart

    def __str__(self):
        return ('{}:{:.08f}@{}{}' if PriceHelper.is_float_price(self.price) else '{}:{}@{}{}').format(
            self.__class__.__name__, self.price, self.vol, ' !!SMART!!' if self.is_smart() else '') + \
        '(abs vol: {:.08f})'.format(self.calculated_volume) if self.vol.is_rel() and self.calculated_volume else ''


    def serializable_dict(self):
        d = OrderedDict()

        if not self.status.is_new():
            d['status'] = self.status

        if self.id:
            d['id'] = self.id

        if self.date:
            d['date'] = self.date

        if PriceHelper.is_float_price(self.price):
            d['price'] = self.format_float(self.price)
        else:
            d['price'] = self.price

        d['vol'] = self.vol

        if self.smart is not None:
            d['smart'] = self.smart

        if self.sl != 0:
            d['sl'] = self.format_float(self.sl)

        if self.best_price > 0:
            d['best_price'] = self.format_float(self.best_price)

        if self.calculated_volume:
            d['calculated_volume'] = self.format_float(self.calculated_volume)

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

        if str(self.price_val).lower() == PriceHelper.CURR_PRICE_TOKEN:
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
        #Issue 21 float parsing
        s = str(price_str).strip().lower().replace(',', '.')
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


class ExitTarget(Target):
    def __init__(self, **kvargs):
        super().__init__(**kvargs)

    def is_exit_target(self):
        return True

class StopLossTarget(Target):
    def __init__(self, **kvargs):
        super().__init__(**kvargs)

    def is_stoploss_target(self):
        return True


class EntryTarget(Target):
    def __init__(self, **kvargs):
        super().__init__(**kvargs)

    def is_entry_target(self):
        return True
