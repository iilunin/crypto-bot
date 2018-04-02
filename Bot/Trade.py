from typing import List
from enum import Enum

from Bot.EntrySettings import EntrySettings
from Bot.StopLossSettings import StopLossSettings
from Bot.Target import *


class Trade:
    class Side(Enum):
        BUY = 'buy'
        SELL = 'sell'

    def __init__(self, symbol, side, asset, targets, sl_settings, status=None, entry=None):
        self.entry = EntrySettings(**entry) if entry else None

        self.side = Trade.Side(side.lower())
        self.symbol = symbol
        self.sl_settings = StopLossSettings(**sl_settings)
        self.asset = asset

        self.targets: List[Target] = []

        self.set_targets(targets)

        if status:
            self.status = OrderStatus(status.lower())
        else:
            self.status = OrderStatus.ACTIVE if not entry else OrderStatus.NEW


    def set_targets(self, targets):
        self.targets.extend([RegularTarget(t) for t in targets])
        self.targets.sort(key=lambda t: t.price, reverse=self.side == Trade.Side.BUY)

    def is_sell_order(self):
        return self.side == Trade.Side.SELL

    def has_entry(self):
        return self.entry is not None

    def get_available_targets(self) -> List[Target]:
        return [t for t in self.targets if not t.is_completed()]

    def get_closed_targets(self) -> List[Target]:
        return [t for t in self.targets if t.is_completed()]

    def get_initial_stop(self) -> Target:
        return self.sl_settings.initial_target

    # TODO: add entry targets
    def get_all_active_placed_targets(self) -> List[Target]:
        tgt = [self.sl_settings.initial_target]
        tgt.extend(self.targets)
        if self.has_entry():
            tgt.append(self.entry.target)

        return [t for t in tgt if not t.is_completed() and t.has_id()]

    def is_completed(self):
        return self.status == OrderStatus.COMPLETED

    def __str__(self):
        return '{}: {}'.format(self.symbol, self.side)

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)

