from enum import Enum

from Bot.CustomSerializable import CustomSerializable
from Bot.Target import StopLossTarget
from Bot.Value import Value


class StopLossSettings(CustomSerializable):
    DEFAULT_ZONE_ENTRY = '0.3%'
    DEFAULT_LIMIT_PRICE = '0.05%'

    class Type(Enum):
        TRAILING = 'trailing'
        FIXED = 'fixed'

    def __init__(self, type, val, initial_target, zone_entry=DEFAULT_ZONE_ENTRY, limit_price_threshold=DEFAULT_LIMIT_PRICE, last_stoploss=0, **kvargs):
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
        d = dict(self.__dict__)

        if not self.last_stoploss:
            d.pop('last_stoploss', None)
        else:
            d['last_stoploss'] = self.format_float(self.last_stoploss)

        if self.limit_price_threshold.get_val(1) == Value(StopLossSettings.DEFAULT_LIMIT_PRICE).get_val(1):
            d.pop('limit_price_threshold', None)

        if self.zone_entry.get_val(1) == Value(StopLossSettings.DEFAULT_ZONE_ENTRY).get_val(1):
            d.pop('zone_entry', None)

        else:
            d['last_stoploss'] = self.format_float(self.last_stoploss)

        return d
