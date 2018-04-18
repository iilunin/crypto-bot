from collections import OrderedDict
from enum import Enum

from Bot.CustomSerializable import CustomSerializable
from Bot.Target import StopLossTarget
from Bot.Value import Value


class StopLossSettings(CustomSerializable):
    DEFAULT_ZONE_ENTRY = '0.3%'
    DEFAULT_LIMIT_PRICE = '0.1%'
    DEFAULT_TRAILING_SL_VALUE = '5%'

    class Type(Enum):
        TRAILING = 'trailing'
        FIXED = 'fixed'

    def __init__(self, initial_target, type=Type.FIXED.name, val=DEFAULT_TRAILING_SL_VALUE,
                 zone_entry=DEFAULT_ZONE_ENTRY, limit_price_threshold=DEFAULT_LIMIT_PRICE, last_stoploss=0,
                 **kvargs):
        self.type = StopLossSettings.Type(type.lower())
        self.val = Value(val)
        self.limit_price_threshold = Value(limit_price_threshold)
        self.zone_entry = Value(zone_entry)
        self.initial_target = StopLossTarget(**initial_target)
        self.last_stoploss = float(last_stoploss)

    def is_trailing(self):
        return self.type == StopLossSettings.Type.TRAILING

    def is_fixed(self):
        return self.type == StopLossSettings.Type.FIXED

    def serializable_dict(self):
        # d = dict(self.__dict__)
        d = OrderedDict()

        d['type'] = self.type

        if self.is_trailing() and self.val != Value(StopLossSettings.DEFAULT_TRAILING_SL_VALUE):
            d['val'] = self.val

        if self.last_stoploss:
            d['last_stoploss'] = self.last_stoploss

        if self.limit_price_threshold != Value(StopLossSettings.DEFAULT_LIMIT_PRICE):
            d['limit_price_threshold'] = self.limit_price_threshold

        if self.zone_entry != Value(StopLossSettings.DEFAULT_ZONE_ENTRY):
            d['zone_entry'] = self.zone_entry

        d['initial_target'] = self.initial_target

        return d
