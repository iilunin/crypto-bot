import json
from json import JSONEncoder, encoder

from Bot.JsonEncoder import CustomJsonEncoder
from Bot.Order import Order


class ConfigLoader:
    def load_new_orders(self, loader):
        raw_orders = loader()
        return [Order(**ro) for ro in raw_orders['orders']]

    def load_json(self, path):
        def load():
            with open(path, 'r') as f:
                return json.load(f)

        return load

    def save_orders(self, path, orders):
        d = {'orders': orders}

        encoder.FLOAT_REPR = lambda o: format(o, '.8f')

        with open(path, 'w') as f:
            json.dump(d, fp=f, cls=CustomJsonEncoder, indent=4)
