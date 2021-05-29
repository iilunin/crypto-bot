from collections import OrderedDict
import uuid
from typing import List
from Bot.EntryExitSettings import EntryExitSettings
from Bot.TradeEnums import Side
from Bot.StopLossSettings import StopLossSettings
from Bot.Target import *


class Trade(CustomSerializable):
    # def __init__(self, symbol, side, asset, status=None, sl_settings=None, entry=None, exit=None):
    def __init__(self, symbol, side, asset, status=None, *args, **kvargs):
        self.side = Side(side.lower())
        self.symbol = symbol.upper()
        self.asset = asset.upper()

        self.entry: EntryExitSettings = None
        self.exit: EntryExitSettings = None

        self._init_entry_exit(True, kvargs.get('entry'), self.side)
        self._init_entry_exit(False, kvargs.get('exit'), self.side)

        sl_settings = kvargs.get('stoploss', kvargs.get('sl_settings'))

        self.sl_settings: StopLossSettings = StopLossSettings(**sl_settings) if sl_settings else None

        if status:
            self.status = OrderStatus(status.lower())
        else:
            self.status = OrderStatus.ACTIVE if not kvargs.get('entry') else OrderStatus.NEW

        self.cap = float(kvargs.get('cap')) if kvargs.get('cap') else None

        self.id = kvargs.get('id', None)

        if not self.id:
            self.id = str(uuid.uuid4())

    def _init_entry_exit(self, is_entry, data, side: Side):
        if data:
            if 'side' not in data:
                data['side'] = (side.reverse() if is_entry else side).value

            # TODO: right now there is only Smart Entry option allowed
            if is_entry:
                data['smart'] = True
                self.entry = EntryExitSettings(is_entry=is_entry, **data)
            else:
                self.exit = EntryExitSettings(is_entry=is_entry, **data)

    def get_cap(self, available_balance):
        return min(self.cap if self.cap else available_balance, available_balance)

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
        d = OrderedDict()

        d['id'] = self.id
        d['asset'] = self.asset
        d['symbol'] = self.symbol
        d['side'] = self.side
        d['status'] = self.status

        if self.cap:
            d['cap'] = self.format_float(self.cap)

        if self.entry:
            d['entry'] = self.entry

        if self.exit:
            d['exit'] = self.exit

        if self.sl_settings:
            d['stoploss'] = self.sl_settings

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

    def is_removed(self):
        return self.status.is_removed()

    def set_active(self):
        self.status = OrderStatus.ACTIVE

    def set_completed(self):
        self.status = OrderStatus.COMPLETED

    def set_removed(self):
        self.status = OrderStatus.REMOVED

    def __str__(self):
        return '{}({}): {}'.format(self.symbol, self.id, self.side)

    def describe(self):
        description = self.__str__()
        if self.has_entry():
            description += '\n'+self.entry.describe()
        if self.has_exit():
            description +='\n'+self.exit.describe()
        if self.has_stoploss():
            description += '\n'+self.sl_settings.describe()
        return description

