from typing import List

from Bot.CustomSerializable import CustomSerializable
from Bot.TradeEnums import Side, Entry
from Bot.Target import EntryTarget, Target, ExitTarget
from Bot.Value import Value


class EntryExitSettings(CustomSerializable):
    def __init__(self,
                 target=None,
                 targets=None,
                 side=None,
                 sl_threshold=None,
                 pullback_threshold=None,
                 type=Entry.TARGET.value,
                 is_entry=True,
                 best_price=0,
                 last_target_smart=True):

        self.last_target_smart = last_target_smart

        self.sl_threshold = Value(sl_threshold) if sl_threshold else None
        self.pullback_threshold = Value(pullback_threshold) if pullback_threshold else self.sl_threshold

        if last_target_smart:
            if not self.sl_threshold:
                self.sl_threshold = Value("1%")
                self.pullback_threshold = Value("1%")
        else:
            if not self.sl_threshold:
                self.sl_threshold = Value("0")

        self.side = Side(side.lower()) if side else None
        self.type = Entry(type.lower())
        self.is_entry = is_entry
        self.best_price = float(best_price)

        self.targets: [Target] = []

        if target:
            self.targets.append(self._create_target(target, is_entry))
        if targets:
            self.set_targets([self._create_target(t, is_entry) for t in targets])

    def set_targets(self, targets):
        self.targets.extend(targets)
        self.targets.sort(key=lambda t: (not t.is_completed(), t.price), reverse=self.side.is_buy())

    def get_completed_targets(self) -> List[Target]:
        return [t for t in self.targets if t.is_completed()]

    def is_completed(self):
        return all(t.is_completed() for t in self.targets)

    def _create_target(self, t, is_entry):
        return EntryTarget(t) if is_entry else ExitTarget(t)

    def serializable_dict(self):
        d = dict(self.__dict__)

        if not self.sl_threshold:
            d.pop('sl_threshold', None)

        if not self.pullback_threshold or str(self.sl_threshold) == str(self.pullback_threshold):
            d.pop('pullback_threshold', None)

        if not self.side:
            d.pop('side', None)
        if self.best_price == 0:
            d.pop('best_price', None)
        else:
            d['best_price'] = '{:.08f}'.format(self.best_price)

        if self.is_entry:
            d.pop('last_target_smart', None)

        d.pop('is_entry', None)

        return d

    # only one smart target for now
    # TODO: make combined TARGETED/SMART approach
    def get_smart_target(self):
        return self.targets[0]

    def is_entry(self):
        return self.is_entry

    def is_exit(self):
        return not self.is_entry
