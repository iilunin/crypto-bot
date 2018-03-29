import time
from json import JSONEncoder

from binance.client import Client
from binance.websockets import BinanceSocketManager
from decimal import getcontext

from Bot.FXConnector import FXConnector
from Bot.Order import Order
from Bot.OrderHandler import OrderHandler
from Bot.OrderStatus import OrderStatus
from Bot.OrderValidator import OrderValidator
from Bot.ConfigLoader import ConfigLoader

def main():
    getcontext().prec = 8
    test_change_order()

def test_change_order():
    cl = ConfigLoader()
    orders = cl.load_new_orders(cl.load_json('orders.json'))
    orders[0].get_available_targets()[0].set_completed()
    orders[0].status = OrderStatus.COMPLETED
    cl.save_orders('orders2.json', orders)

    orders = cl.load_new_orders(cl.load_json('orders2.json'))

def test_start_app():
    cl = ConfigLoader()
    orders = cl.load_new_orders(cl.load_json('orders.json'))
    ov = OrderValidator()

    for o in orders[:]:
        if not ov.validate(o):
            print(ov.errors)
            print(ov.warnings)
            orders.remove(o)

    api = cl.load_json('api.json')()
    handler = OrderHandler(orders, FXConnector(api['key'], api['secret']))
    handler.start_listening()

if __name__ == '__main__':
    main()
