import logging

from Bot.FXConnector import FXConnector
from Bot.OrderHandler import OrderHandler
from Bot.OrderEnums import OrderStatus
from Bot.OrderValidator import OrderValidator
from Bot.ConfigLoader import ConfigLoader

from Bot.Strategy.SmartOrder import SmartOrder

ORDER_PATH = 'trades.json'
ORDER_PATH_PORTFOLIO = 'trades_portfolio.json'
ORDER_PATH_UPD = 'trades.json'

logging.basicConfig(level=logging.INFO)

def main():
    # test_change_order()
    # res = get_historical_klines('LTCBTC', '1d', 'December 21, 2017', 'December 21, 2017')
    # print(res)
    # test_smart_order()
    test_start_app(ORDER_PATH_PORTFOLIO)
    # test_change_order()


def test_change_order():
    cl = ConfigLoader()
    orders = cl.load_order_list(cl.json_loader('trades.json'))


    # orders[0].get_available_targets()[0].set_completed()
    # orders[0].status = OrderStatus.COMPLETED
    cl.save_orders(cl.json_saver('trades2.json'), orders)

    orders = cl.load_order_list(cl.json_loader('trades2.json'))

def test_smart_order():
    price_change = []
    price_change.extend(range(490, 465, -1))
    price_change.extend(range(471, 479, 1))
    price_change.extend(range(478, 463, -1))
    price_change.extend(range(463, 473, 1))
    so = SmartOrder(True, 475)
    for p in price_change:
        so.price_update(p)

    print('-' * 20)
    print('-' * 20)

    price_change = []
    price_change.extend(range(480, 474, -1))
    price_change.extend(range(476, 480, 1))
    so = SmartOrder('TRXBTC', 475)
    for p in price_change:
        so.price_update(p)

def test_start_app(path=ORDER_PATH):
    cl = ConfigLoader()

    o_loader = cl.json_loader(path)
    o_saver = cl.json_saver(path)
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
