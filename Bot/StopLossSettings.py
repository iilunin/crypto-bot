from enum import Enum

from Bot.Target import StopLossTarget
from Bot.Value import Value


class StopLossSettings:

    class Type(Enum):
        TRAILING = 'trailing'
        FIXED = 'fixed'

    def __init__(self, type, val, threshold, initial_target, limit_price_threshold=Value("0.05%")):
        self.type = StopLossSettings.Type(type.lower())
        self.val = Value(val)
        self.limit_price_threshold = Value(limit_price_threshold)
        self.threshold = Value(threshold)
        self.initial_target = StopLossTarget(initial_target)

    def is_trailing(self):
        return self.type == StopLossSettings.Type.TRAILING

    def is_fixed(self):
        return self.type == StopLossSettings.Type.FIXED
