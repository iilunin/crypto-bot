from typing import List
from Bot.EntryExitSettings import EntryExitSettings
from Bot.TradeEnums import Side
from Bot.StopLossSettings import StopLossSettings
from Bot.Target import *


class Trade(CustomSerializable):
    def __init__(self, symbol, side, asset, sl_settings=None, status=None, entry=None, exit=None):

        self.side = Side(side.lower())
        self.symbol = symbol.upper()
        self.asset = asset.upper()

        self.entry: EntryExitSettings = None
        self.exit: EntryExitSettings = None

        self._init_entry_exit(True, entry, self.side)
        self._init_entry_exit(False, exit, self.side)

        self.sl_settings = StopLossSettings(**sl_settings) if sl_settings else None

        if status:
            self.status = OrderStatus(status.lower())
        else:
            self.status = OrderStatus.ACTIVE if not entry else OrderStatus.NEW

    def _init_entry_exit(self, is_entry, data, side: Side):
        if data:
            if 'side' not in data:
                data['side'] = (side.reverse() if is_entry else side).value

            if is_entry:
                self.entry = EntryExitSettings(is_entry=is_entry, **data)
            else:
                self.exit = EntryExitSettings(is_entry=is_entry, **data)

    def is_sell(self):
        return self.side.is_sell()

    def has_entry(self):
        return self.entry is not None

    def has_exit(self):
        return self.exit is not None

    def has_stoploss(self):
        return self.sl_settings is not None and self.sl_settings.initial_target

    def get_closed_targets(self) -> List[Target]:
        return [t for t in self.targets if t.is_completed()]

    def get_initial_stop(self) -> Target:
        if self.sl_settings:
            return self.sl_settings.initial_target
        return None

    def serializable_dict(self):
        d = dict(self.__dict__)
        if not self.sl_settings:
            d.pop('sl_settings', None)
        if not self.entry:
            d.pop('entry', None)
        if not self.exit:
            d.pop('exit', None)
        return d

    def get_all_active_placed_targets(self) -> List[Target]:
        tgt = []
        if self.has_exit():
            tgt.extend(self.exit.targets)
        if self.has_entry():
            tgt.extend(self.entry.targets)
        if self.has_stoploss():
            tgt.append(self.sl_settings.initial_target)

        return [t for t in tgt if not t.is_completed() and t.has_id()]

    def is_completed(self):
        return self.status.is_completed()

    def is_active(self):
        return self.status.is_active()

    def is_new(self):
        return self.status.is_new()

    def set_active(self):
        self.status = OrderStatus.ACTIVE

    def set_completed(self):
        self.status = OrderStatus.COMPLETED

    def __str__(self):
        return '{}: {}'.format(self.symbol, self.side)

