from enum import Enum

from Bot.Target import StopLossTarget
from Bot.Value import Value


class StopLossSettings:

    class Type(Enum):
        TRAILING = 'trailing'
        FIXED = 'fixed'

    def __init__(self, type, val, threshold, initial_target):
        self.type = StopLossSettings.Type(type.lower())
        self.val = Value(val)
        self.threshold = threshold
        self.initial_target = StopLossTarget(initial_target)

