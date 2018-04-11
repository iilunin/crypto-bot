from enum import Enum

from Bot.CustomSerializable import CustomSerializable
from Bot.Target import StopLossTarget
from Bot.Value import Value


class StopLossSettings(CustomSerializable):

    class Type(Enum):
        TRAILING = 'trailing'
        FIXED = 'fixed'

    def __init__(self, type, val, threshold, initial_target, limit_price_threshold=Value("0.05%"), last_stoploss=0):
        self.type = StopLossSettings.Type(type.lower())
        self.val = Value(val)
        self.limit_price_threshold = Value(limit_price_threshold)
        self.threshold = Value(threshold)
        self.initial_target = StopLossTarget(initial_target)
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

        return d
