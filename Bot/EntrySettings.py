from Bot.OrderEnums import Side
from Bot.Target import EntryTarget
from Bot.Value import Value


class EntrySettings:
    def __init__(self, target, side=None, sl_threshold=None, pullback_threshold=None):
        self.target = EntryTarget(target)
        self.sl_threshold = Value(sl_threshold) if sl_threshold else None
        self.pullback_threshold = Value(pullback_threshold) if pullback_threshold else None
        self.side = Side(side.lower()) if side else None
