import json
import os

from os import listdir
from os.path import isfile, join

import Utils
from Bot.JsonEncoder import CustomJsonEncoder
from Bot.Trade import Trade
from Utils.Utils import get_symbol_and_id_from_file_path


class ConfigLoader:
    PARENT_ELEMENT = 'trades'
    ALT_PARENT_ELEMENT = 'trade'

    def json_loader(self, path):
        def load():
            with open(path, 'r') as f:
                return json.load(f)

        return load

    def advanced_loader(self, path):
        def load():
            target_path_list = [f for f in listdir(path) if isfile(join(path, f)) and f.lower().endswith('json')]
            trades = []
            d = {ConfigLoader.PARENT_ELEMENT: trades}
            for t_path in target_path_list:
                with open(join(path, t_path), 'r') as f:
                    trade_obj = json.load(f)[ConfigLoader.PARENT_ELEMENT]
                    trades.extend(trade_obj)
            return d

        return load

    def json_saver(self, path):
        def save(obj):
            with open(path() if callable(path) else path, 'w') as f:
                json.dump(obj, fp=f, cls=CustomJsonEncoder, indent=2)

        return save

    @classmethod
    def get_json_str(cls, obj):
        return json.dumps(obj, cls=CustomJsonEncoder, indent=2)

    # def advanced_saver(self, path):
    #     def save(obj):
    #         with open(path, 'w') as f:
    #             json.dump(obj, fp=f, cls=CustomJsonEncoder, indent=4)

    def load_trade_list(self, path):
        if isfile(path):
            trades = self.load_trade_list_fromfile(path)

            if self._rename_trade_file(os.path.split(path)[0], path, trades):
                os.remove(path)

            return trades

        target_path_list = [f for f in listdir(path) if isfile(join(path, f)) and f.lower().endswith('json')]
        trades = []
        for t_path in target_path_list:
            full_path = join(path, t_path)
            trades_from_file = self.load_trade_list_fromfile(full_path)
            trades.extend(trades_from_file)
            if len(trades_from_file) > 0:
                if self._rename_trade_file(path, t_path, trades_from_file):
                    os.remove(full_path)

        return trades

    def _rename_trade_file(self, path, file_name, trades):
        symbol, id = get_symbol_and_id_from_file_path(file_name)
        if isinstance(trades, Trade):
            trades = [trades]

        update_file_name = False
        for trade in trades:
            if id is None or (symbol != trade.symbol and id != trade.id):
                self.save_trades(self.json_saver(join(path, '{}_{}.json'.format(trade.symbol, trade.id))), trade)
                update_file_name = True
        return update_file_name

    def load_trade_list_fromfile(self, file_path):
        with open(file_path, 'r') as f:
            trade_obj = json.load(f)
            if ConfigLoader.PARENT_ELEMENT in trade_obj:
                return [Trade(**to) for to in trade_obj[ConfigLoader.PARENT_ELEMENT]]
            if ConfigLoader.ALT_PARENT_ELEMENT in trade_obj:
                return [Trade(**trade_obj[ConfigLoader.ALT_PARENT_ELEMENT])]

    def save_trades(self, saver, trades):
        if isinstance(trades, list):
            parent = ConfigLoader.ALT_PARENT_ELEMENT if len(trades) == 1 else ConfigLoader.PARENT_ELEMENT

            if len(trades) == 1:
                trades = trades[0]
        else:
            parent = ConfigLoader.ALT_PARENT_ELEMENT

        d = {parent: trades}
        saver(d)

    def persist_updated_trade(self, trade: Trade, saver):
        #TODO: don't need to read file as there is only 1 trade per file at the moment
        # old_trades = self.load_trade_list(loader)
        # old_order = next(o for o in old_trades if o.symbol == trade.symbol)
        # old_trades.remove(old_order)
        # old_trades.append(trade)
        #
        # old_trades.sort(key=lambda trade: trade.symbol)
        # self.save_trades(saver, old_trades)

        self.save_trades(saver, trade)



