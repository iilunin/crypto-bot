from Bot.Target import EntryTarget
from Bot.Value import Value


class EntrySettings:
    def __init__(self, target, sl_threshold=None, pullback_threshold=None):
        self.target = EntryTarget(target)
        self.sl_threshold = Value(sl_threshold) if sl_threshold else None
        self.pullback_threshold = Value(pullback_threshold) if pullback_threshold else None
