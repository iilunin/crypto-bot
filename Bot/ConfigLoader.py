import json
from json import JSONEncoder, encoder

from Bot.JsonEncoder import CustomJsonEncoder
from Bot.Trade import Trade


class ConfigLoader:
    PARENT_ELEMENT = 'trades'

    def json_loader(self, path):
        def load():
            with open(path, 'r') as f:
                return json.load(f)

        return load

    def json_saver(self, path):
        def save(obj):
            with open(path, 'w') as f:
                json.dump(obj, fp=f, cls=CustomJsonEncoder, indent=4)

        return save

    def load_order_list(self, loader):
        raw_orders = loader()
        return [Trade(**ro) for ro in raw_orders[ConfigLoader.PARENT_ELEMENT]]

    def save_orders(self, saver, orders):
        d = {ConfigLoader.PARENT_ELEMENT: orders}
        saver(d)

    def persist_updated_order(self, order: Trade, loader, saver):
        old_orders = self.load_order_list(loader)
        old_order = next(o for o in old_orders if o.symbol == order.symbol)
        old_orders.remove(old_order)
        old_orders.append(order)
        self.save_orders(saver, old_orders)



