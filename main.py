import logging

from Bot.FXConnector import FXConnector
from Bot.OrderHandler import OrderHandler
from Bot.OrderStatus import OrderStatus
from Bot.OrderValidator import OrderValidator
from Bot.ConfigLoader import ConfigLoader


from binance.client import Client
from datetime import datetime, date

from hist_data import get_historical_klines

ORDER_PATH = 'trades.json'
ORDER_PATH_UPD = 'trades.json'

logging.basicConfig(level=logging.INFO)

def main():
    # test_change_order()
    # res = get_historical_klines('LTCBTC', '1d', 'December 21, 2017', 'December 21, 2017')
    # print(res)
    test_start_app()


def test_change_order():
    cl = ConfigLoader()
    orders = cl.load_order_list(cl.json_loader('trades.json'))
    orders[0].get_available_targets()[0].set_completed()
    orders[0].status = OrderStatus.COMPLETED
    cl.save_orders('orders2.json', orders)

    orders = cl.load_order_list(cl.json_loader('orders2.json'))

def test_start_app():
    cl = ConfigLoader()

    o_loader = cl.json_loader(ORDER_PATH)
    o_saver = cl.json_saver(ORDER_PATH)
    orders = cl.load_order_list(o_loader)
    ov = OrderValidator()

    for o in orders[:]:
        if not ov.validate(o):
            print(ov.errors)
            print(ov.warnings)
            orders.remove(o)

    api = cl.json_loader('api.json')()
    handler = OrderHandler(
        orders,
        FXConnector(api['key'], api['secret']),
        lambda order: cl.persist_updated_order(order, o_loader, o_saver)
    )

    handler.start_listening()

if __name__ == '__main__':
    main()
