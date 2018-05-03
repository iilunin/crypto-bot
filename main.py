# import atexit
import signal

from os.path import isfile, join
from os import listdir, environ

import sys

from Bot.Target import Target
from ConsoleLauncher import ConsoleLauncher
from Bot.ConfigLoader import ConfigLoader

from Bot.Strategy.SmartOrder import SmartOrder

TRADE_FILE_PATH_PATTERN = '{}{}.json'

TEST_PORTFOLIO_PATH = environ.get('TRADE_DIR', 'Trades/Test/')


TRADE_PORTFOLIO_PATH = environ.get('TRADE_DIR', 'Trades/Portfolio/')
COMPLETED_ORDER_PATH_PORTFOLIO = environ.get('TRADE_COMPLETED_DIR', 'Trades/Completed/')
CONF_DIR = environ.get('CONF_DIR', 'Conf/')

ENABLE_CLOUD = True

launcher = ConsoleLauncher(
    TRADE_PORTFOLIO_PATH,
    COMPLETED_ORDER_PATH_PORTFOLIO,
    CONF_DIR,
    environ.get('TRADE_BUCKET') is not None and ENABLE_CLOUD)
# launcher = ConsoleLauncher(TEST_PORTFOLIO_PATH, COMPLETED_ORDER_PATH_PORTFOLIO, CONF_DIR, False)

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == 'sync':
            launcher.sync_down()
            return

        elif sys.argv[1] == 'gen':
            get_input_for_targets()
            return

    launcher.start_bot()

# def signal_handler(signal=None, frame=None):
#     launcher.stop_bot()

def get_input_for_targets():
    smart = 'y'
    if len(sys.argv) > 2:
        single_arg = sys.argv[2]
        args = single_arg.split('/', 4)
        price = args[0]
        iter = args[1]
        increment = args[2]
        if len(args) == 4:
            smart = args[3]
    else:
        price = get_input("Start price: ")
        iter = get_input("Iterations (5): ", 5)
        increment = get_input("Price increase in percent (2): ", 2)
        smart = get_input("Smart (Y/n):", 'y')

    smart = True if not smart or smart.lower() == 'y' else False

    generate_targets(float(price), int(iter), float(increment), smart)

def get_input(text, default=None):
    inp = input(text)
    if not inp:
        return default
    if not inp.strip():
        return default
    return inp.strip()

def generate_targets(start_price, iter=4, increment=4, smart=True):
    targets = []
    for i in range(0, iter):
        vol = round(100/(iter - i), 2)
        targets.append(Target(price=start_price, vol='{}%'.format(vol), smart=smart))
        start_price = round(start_price * (1+increment/100), 8)

    print(ConfigLoader.get_json_str(targets))


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
    so = SmartOrder(True, 467)

    print('BUY Order')
    for p in price_change:
        print('Price: {}, SL {}'.format(p, so.price_update(p)))

    print('SELL Order')
    so = SmartOrder(False, 475)
    for p in price_change:
        print('Price: {}, SL {}'.format(p, so.price_update(p)))

    print('-' * 20)
    print('-' * 20)

    price_change = []
    price_change.extend(range(480, 474, -1))
    price_change.extend(range(476, 480, 1))
    so = SmartOrder(True, 475)
    for p in price_change:
        print('Price: {}, SL {}'.format(p, so.price_update(p)))

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

# @atexit.register
# def on_exit():
#     # print('on exit')
#     try:
#         if launcher:
#             launcher.stop_bot()
#     except Exception as e:
#         print(e)


if __name__ == '__main__':
    main()
