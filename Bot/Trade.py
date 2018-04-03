from typing import List
from enum import Enum

from Bot.EntrySettings import EntrySettings
from Bot.OrderEnums import Side
from Bot.StopLossSettings import StopLossSettings
from Bot.Target import *


class Trade:
    def __init__(self, symbol, side, asset, targets=None, sl_settings=None, status=None, entry=None):
        self.entry = EntrySettings(**entry) if entry else None

        self.side = Side(side.lower())
        self.symbol = symbol
        self.sl_settings = StopLossSettings(**sl_settings) if sl_settings else None
        self.asset = asset

        self.targets: List[Target] = []

        if targets:
            self.set_targets(targets)

        if status:
            self.status = OrderStatus(status.lower())
        else:
            self.status = OrderStatus.ACTIVE if not entry else OrderStatus.NEW


    def set_targets(self, targets):
        self.targets.extend([RegularTarget(t) for t in targets])
        self.targets.sort(key=lambda t: t.price, reverse=self.side == Side.BUY)

    def is_sell_order(self):
        return self.side == Side.SELL

    def has_entry(self):
        return self.entry is not None

    def has_stoploss(self):
        return self.sl_settings is not None and self.sl_settings.initial_target

    def has_targets(self):
        return len(self.targets) > 0

    def get_available_targets(self) -> List[Target]:
        return [t for t in self.targets if not t.is_completed()]

    def get_closed_targets(self) -> List[Target]:
        return [t for t in self.targets if t.is_completed()]

    def get_initial_stop(self) -> Target:
        if self.sl_settings:
            return self.sl_settings.initial_target
        return None

    # TODO: add entry targets
    def get_all_active_placed_targets(self) -> List[Target]:
        tgt = []
        if self.has_targets():
            tgt.extend(self.targets)
        if self.has_entry():
            tgt.append(self.entry.target)
        if self.has_stoploss():
            tgt.append(self.sl_settings.initial_target)

        return [t for t in tgt if not t.is_completed() and t.has_id()]

    def is_completed(self):
        return self.status == OrderStatus.COMPLETED

    def set_active(self):
        self.status = OrderStatus.ACTIVE

    def __str__(self):
        return '{}: {}'.format(self.symbol, self.side)

