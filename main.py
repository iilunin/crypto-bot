import logging
import atexit
import os

from os.path import isfile, join

from os import listdir

from datetime import datetime
from threading import Timer

from Bot.FXConnector import FXConnector
from Bot.OrderHandler import OrderHandler
from Bot.TradeEnums import OrderStatus
from Bot.OrderValidator import OrderValidator
from Bot.ConfigLoader import ConfigLoader

from Bot.Strategy.SmartOrder import SmartOrder
from Bot.Trade import Trade

TRADE_FILE_PATH_PATTERN = '{}{}.json'

NEW_ORDER_PATH_PORTFOLIO = 'Trades/Portfolio/'
# NEW_ORDER_PATH_PORTFOLIO = 'Trades/NewPortfolio/'

COMPLETED_ORDER_PATH_PORTFOLIO = 'Trades/Completed/'
ORDER_PATH = 'trades.json'
ORDER_PATH_UPD = 'trades.json'

LOG_FORMAT = '%(asctime)s[%(levelname)s][%(name)s]: %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

cl = ConfigLoader()
handler: OrderHandler = None
file_watch_timer: Timer = None
file_watch_list = {}

def main():
    # test_change_order()
    # res = get_historical_klines('LTCBTC', '1d', 'December 21, 2017', 'December 21, 2017')
    # print(res)
    # test_smart_order()
    test_start_app(NEW_ORDER_PATH_PORTFOLIO)
    # save_new_order_file_structure(path=NEW_ORDER_PATH_PORTFOLIO, new_path='Trades/NewPortfolio/')
    # test_change_order()


def test_change_order():
    cl = ConfigLoader()
    orders = cl.load_trade_list(cl.json_loader('trades.json'))


    # orders[0].get_available_targets()[0].set_completed()
    # orders[0].status = OrderStatus.COMPLETED
    cl.save_trades(cl.json_saver('trades2.json'), orders)

    orders = cl.load_trade_list(cl.json_loader('trades2.json'))

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

def save_new_order_file_structure(path, new_path):

    target_path_list = [f for f in listdir(path) if isfile(join(path, f)) and f.lower().endswith('json')]
    for t_path in target_path_list:
        cl = ConfigLoader()
        o_loader = cl.json_loader(join(path, t_path))
        trades = cl.load_trade_list(o_loader)

        for t in trades:
            if t.is_completed():
                continue

            new_trade_path = new_path + t.symbol + '.json'
            cl.save_trades(cl.json_saver(new_trade_path), [t])

def test_start_app(path=ORDER_PATH):
    o_loader = cl.advanced_loader(path)
    # o_saver = cl.json_saver(path)
    trades = cl.load_trade_list(o_loader)
    ov = OrderValidator()

    for trade in trades[:]:
        if trade.is_completed():
            move_completed_trade(trade.symbol)
        if not ov.validate(trade):
            print(trade.symbol)
            print(ov.errors)
            if len(ov.warnings) > 0:
                print(ov.warnings)
            trades.remove(trade)

    api = cl.json_loader('api.json')()

    global handler
    handler = OrderHandler(
        trades,
        FXConnector(api['key'], api['secret']),
        lambda trade: update_trade(trade, cl, path)
    )
    start_timer()
    handler.start_listening()

def update_trade(trade: Trade, cl: ConfigLoader, path):

    file = TRADE_FILE_PATH_PATTERN.format(path, trade.symbol)

    global file_watch_list
    cl.persist_updated_trade(trade,
                             cl.json_loader(file),
                             cl.json_saver(file))

    file_watch_list[file] = os.stat(file).st_mtime


    if trade.is_completed():
        move_completed_trade(trade.symbol)

def move_completed_trade(symbol):
    os.rename(TRADE_FILE_PATH_PATTERN.format(NEW_ORDER_PATH_PORTFOLIO, symbol),
              TRADE_FILE_PATH_PATTERN.format(COMPLETED_ORDER_PATH_PORTFOLIO, datetime.now().strftime('%Y-%m-%d_%H-%M-') + symbol))

@atexit.register
def on_exit():
    print('on exit')
    # global handler
    # if handler:
    #     handler.stop_listening()

    stop_timer()


def start_timer():
    global file_watch_timer
    file_watch_timer = Timer(5, check_files_changed)
    file_watch_timer.start()

def stop_timer():
    global file_watch_timer
    if file_watch_timer:
        file_watch_timer.cancel()
        file_watch_timer = None



def check_files_changed():
    try:
        path = NEW_ORDER_PATH_PORTFOLIO

        global file_watch_list, handler, cl


        target_path_list = [f for f in listdir(path) if isfile(join(path, f)) and f.lower().endswith('json')]
        for t_path in target_path_list:
            file = join(path, t_path)

            current_mtime = os.stat(file).st_mtime

            if file in file_watch_list:
                if not file_watch_list[file] == current_mtime:
                    trades = cl.load_trade_list(cl.json_loader(file))
                    for t in trades:
                        handler.updated_trade(t)
                    print('File "{}" changed'.format(file))

            file_watch_list[file] = os.stat(file).st_mtime
    except Exception as e:
        print(e)
    finally:
        start_timer()



if __name__ == '__main__':
    main()
