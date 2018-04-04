import json

from os import listdir
from os.path import isfile, join

from Bot.JsonEncoder import CustomJsonEncoder
from Bot.Trade import Trade


class ConfigLoader:
    PARENT_ELEMENT = 'trades'

    def json_loader(self, path):
        def load():
            with open(path, 'r') as f:
                return json.load(f)

        return load

    def advanced_loader(self, path):
        def load():
            target_path_list = [f for f in listdir(path) if isfile(join(path, f)) and f.lower().endswith('json')]
            targets = []
            d = {ConfigLoader.PARENT_ELEMENT: targets}
            for t_path in target_path_list:
                with open(join(path, t_path), 'r') as f:
                    targets.extend(json.load(f)[ConfigLoader.PARENT_ELEMENT])
            return d

        return load

    def json_saver(self, path):
        def save(obj):
            with open(path() if callable(path) else path, 'w') as f:
                json.dump(obj, fp=f, cls=CustomJsonEncoder, indent=4)

        return save

    # def advanced_saver(self, path):
    #     def save(obj):
    #         with open(path, 'w') as f:
    #             json.dump(obj, fp=f, cls=CustomJsonEncoder, indent=4)

    def load_trade_list(self, loader):
        raw_orders = loader()
        return [Trade(**ro) for ro in raw_orders[ConfigLoader.PARENT_ELEMENT]]

    def save_trades(self, saver, trades):
        d = {ConfigLoader.PARENT_ELEMENT: trades}
        saver(d)

    def persist_updated_trade(self, trade: Trade, loader, saver):
        old_trades = self.load_trade_list(loader)
        old_order = next(o for o in old_trades if o.symbol == trade.symbol)
        old_trades.remove(old_order)
        old_trades.append(trade)

        old_trades.sort(key=lambda trade: trade.symbol)
        self.save_trades(saver, old_trades)



