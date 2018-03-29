from typing import List
from enum import Enum
import json

from Bot.StopLossSettings import StopLossSettings
from Bot.Target import *


class Order:

    class Side(Enum):
        BUY = 'buy'
        SELL = 'sell'

    def __init__(self, symbol, side, asset, status, vol, entry, targets, sl_settings):
        self.entry = entry
        self.vol = vol
        self.status = OrderStatus(status.lower())
        self.side = Order.Side(side.lower())
        self.symbol = symbol
        self.sl_settings = StopLossSettings(**sl_settings)
        self.asset = asset

        self.targets: List[Target] = []

        self.set_targets(targets)

    def set_targets(self, targets):
        self.targets.extend([RegularTarget(t) for t in targets])
        self.targets.sort(key=lambda t: t.price, reverse=self.side == Order.Side.BUY)


    def is_sell_order(self):
        return self.side == Order.Side.SELL

    def get_available_targets(self) -> List[Target]:
        return [t for t in self.targets if not t.is_completed()]

    def get_closed_targets(self) -> List[Target]:
        return [t for t in self.targets if t.is_completed()]

    def get_initial_stop(self) -> Target:
        return self.sl_settings.initial_target

    def is_completed(self):
        return self.status == OrderStatus.COMPLETED

    def __str__(self):
        return '{}: {}. {}'.format(self.symbol, self.side, self.vol)

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)

