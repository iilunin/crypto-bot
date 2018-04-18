from typing import List

from Bot.CustomSerializable import CustomSerializable
from Bot.TradeEnums import Side
from Bot.Target import EntryTarget, Target, ExitTarget
from Bot.Value import Value


class EntryExitSettings(CustomSerializable):
    DEFAULT_THRESHOLD = Value("1%")

    def __init__(self,
                 targets=None,
                 side=None,
                 sl_threshold=None,
                 is_entry=True,
                 smart=False,
                 **kvargs):

        if 'threshold' in kvargs:
            sl_threshold = kvargs.get('threshold')

        self.sl_threshold = Value(sl_threshold) if sl_threshold else None

        if not self.sl_threshold:
            if smart:
                self.sl_threshold = EntryExitSettings.DEFAULT_THRESHOLD
            else:
                self.sl_threshold = Value("0")

        self.side = Side(side.lower()) if side else None
        self.smart = smart
        self.is_entry = is_entry
        # self.best_price = float(best_price)

        self.targets: [Target] = []

        # As an alternative to specifiying array of targets
        if 'target' in kvargs:
            self.targets.append(self._create_target(kvargs.get('target'), is_entry))

        if targets:
            self.set_targets([self._create_target(t, is_entry) for t in targets])

    def set_targets(self, targets):
        self.targets.extend(targets)
        self.targets.sort(key=lambda t: (not t.is_completed(), t.price), reverse=self.side.is_buy())

    def get_completed_targets(self) -> List[Target]:
        return [t for t in self.targets if t.is_completed()]

    def get_all_smart_targets(self) -> List[Target]:
        return [t for t in self.targets if t.is_smart()]

    def get_all_incomplete_smart_targets(self) -> List[Target]:
        return [t for t in self.targets if t.is_smart() and not t.is_completed()]

    def is_completed(self):
        return all(t.is_completed() for t in self.targets)

    def _create_target(self, t, is_entry):
        return EntryTarget(**t, parent_smart=self.smart) if is_entry else ExitTarget(**t, parent_smart=self.smart)

    def serializable_dict(self):
        d = dict(self.__dict__)

        if not self.sl_threshold:
            d.pop('sl_threshold', None)
            d.pop('threshold', None)
        else:
            d['threshold'] = self.sl_threshold
            d.pop('sl_threshold', None)

        if not self.side:
            d.pop('side', None)

        if self.is_entry:
            d.pop('last_target_smart', None)

        d.pop('is_entry', None)

        return d

    def is_entry(self):
        return self.is_entry

    def is_exit(self):
        return not self.is_entry
