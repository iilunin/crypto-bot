from time import sleep

from retrying import retry

from binance.client import Client
from binance.websockets import BinanceSocketManager
from decimal import Decimal, ROUND_UP, ROUND_DOWN

MAX_ATTEMPTS = 3
DELAY = 1000

class FXConnector:

    class ExchangeInfo:
        def __init__(self, minPrice, maxPrice, tickSize, minQty, maxQty, stepSize, minNotional):
            self.minNotional = Decimal(self.strip_zeros(minNotional))
            self.stepSize = Decimal(self.strip_zeros(stepSize))
            self.maxQty = Decimal(self.strip_zeros(maxQty))
            self.minQty = Decimal(self.strip_zeros(minQty))
            self.tickSize = Decimal(self.strip_zeros(tickSize))
            self.maxPrice = Decimal(self.strip_zeros(maxPrice))
            self.minPrice = Decimal(self.strip_zeros(minPrice))

        def strip_zeros(self, s):
            return s.rstrip('0')

        def adjust_quanity(self, q, round_down=True):
            return float(Decimal(q).quantize(self.stepSize, rounding=ROUND_DOWN if round_down else ROUND_UP))

        def adjust_price(self, q, round_down=True):
            return float(round(Decimal(q), 8).quantize(self.tickSize, rounding=ROUND_DOWN if round_down else ROUND_UP))


    ORDER_STATUS_NEW = 'NEW'
    ORDER_STATUS_PARTIALLY_FILLED = 'PARTIALLY_FILLED'
    ORDER_STATUS_FILLED = 'FILLED'
    ORDER_STATUS_CANCELED = 'CANCELED'
    ORDER_STATUS_PENDING_CANCEL = 'PENDING_CANCEL'
    ORDER_STATUS_REJECTED = 'REJECTED'
    ORDER_STATUS_EXPIRED = 'EXPIRED'

    SIDE_BUY = 'BUY'
    SIDE_SELL = 'SELL'

    ORDER_TYPE_LIMIT = 'LIMIT'
    ORDER_TYPE_MARKET = 'MARKET'
    ORDER_TYPE_STOP_LOSS = 'STOP_LOSS'
    ORDER_TYPE_STOP_LOSS_LIMIT = 'STOP_LOSS_LIMIT'
    ORDER_TYPE_TAKE_PROFIT = 'TAKE_PROFIT'
    ORDER_TYPE_TAKE_PROFIT_LIMIT = 'TAKE_PROFIT_LIMIT'
    ORDER_TYPE_LIMIT_MAKER = 'LIMIT_MAKER'

    TIME_IN_FORCE_GTC = 'GTC'  # Good till cancelled
    TIME_IN_FORCE_IOC = 'IOC'  # Immediate or cancel
    TIME_IN_FORCE_FOK = 'FOK'  # Fill or kill

    ORDER_RESP_TYPE_ACK = 'ACK'
    ORDER_RESP_TYPE_RESULT = 'RESULT'
    ORDER_RESP_TYPE_FULL = 'FULL'

    def __init__(self, key=None, secret=None):
        self.client = Client(key, secret)
        self.bs = None
        # self.connection = None
        self.ticker_connection = None
        self.user_data_connection = None

    def listen_symbols(self, symbols, socket_handler, user_data_handler):
        self.bs = BinanceSocketManager(self.client)
        self.stop_listening()

        # self.connection = self.bs.start_multiplex_socket(['{}@trade'.format(s.lower()) for s in symbols],
        #                                                  socket_handler)

        self.ticker_connection = self.bs.start_multiplex_socket(['{}@ticker'.format(s.lower()) for s in symbols],
                                                         socket_handler)
        self.user_data_connection = self.bs.start_user_socket(user_data_handler)

    def start_listening(self):
        self.bs.start()

    def stop_listening(self):
        if self.ticker_connection:
            # self.bs.stop_socket(self.connection)
            self.bs.stop_socket(self.ticker_connection)
            self.bs.stop_socket(self.user_data_connection)

    def cancel_order(self, sym, id):
        return self.client.cancel_order(symbol=sym, orderId=id)

    def get_open_orders(self, sym):
        return [o['orderId'] for o in self.client.get_open_orders(symbol=sym)]

    @retry(stop_max_attempt_number=MAX_ATTEMPTS, wait_fixed=DELAY)
    def get_all_orders(self, sym, limit=500):
        return {o['orderId']: {'status': o['status'],
                               'price': o['price'],
                               'stop_price': o['stopPrice'],
                               'vol': o['origQty'],
                               'vol_exec': o['executedQty']}
                for o in self.client.get_all_orders(symbol=sym, limit=limit)}


    @retry(stop_max_attempt_number=MAX_ATTEMPTS, wait_fixed=DELAY)
    def get_all_tickers(self):
        return self.client.get_all_tickers()

    @retry(stop_max_attempt_number=MAX_ATTEMPTS, wait_fixed=DELAY)
    def get_orderbook_tickers(self):
        return self.client.get_orderbook_tickers()

    @retry(stop_max_attempt_number=MAX_ATTEMPTS, wait_fixed=DELAY)
    def get_order_status(self, id):
        return self.client.get_order(orderId=id)

    # @retry(stop_max_attempt_number=MAX_ATTEMPTS, wait_fixed=DELAY)
    def create_makret_order(self, sym, side, volume):
        return self.client.create_order(
            symbol=sym,
            side=side,
            type=FXConnector.ORDER_TYPE_MARKET,
            quantity=FXConnector.format_number(volume))

    # @retry(stop_max_attempt_number=MAX_ATTEMPTS, wait_fixed=DELAY)
    def create_limit_order(self, sym, side, price, volume):
        return self.client.create_order(
            symbol=sym,
            side=side,
            type=FXConnector.ORDER_TYPE_LIMIT,
            timeInForce=FXConnector.TIME_IN_FORCE_GTC,
            quantity=FXConnector.format_number(volume),
            price=FXConnector.format_number(price))

    # @retry(stop_max_attempt_number=MAX_ATTEMPTS, wait_fixed=DELAY)
    def create_stop_order(self, sym, side, stop_price, price, volume):
        return self.client.create_order(
            symbol=sym,
            side=side,
            type=FXConnector.ORDER_TYPE_STOP_LOSS_LIMIT,
            timeInForce=FXConnector.TIME_IN_FORCE_GTC,
            quantity=FXConnector.format_number(volume),
            stopPrice=FXConnector.format_number(stop_price),
            price=FXConnector.format_number(price))

    # @retry(stop_max_attempt_number=MAX_ATTEMPTS, wait_fixed=DELAY)
    def create_test_stop_order(self, sym, side, price, volume):
        return self.client.create_test_order(
            symbol=sym,
            side=side,
            type=FXConnector.ORDER_TYPE_STOP_LOSS_LIMIT,
            timeInForce=FXConnector.TIME_IN_FORCE_GTC,
            quantity=FXConnector.format_number(volume),
            stopPrice=FXConnector.format_number(price),
            price=FXConnector.format_number(price))

    @retry(stop_max_attempt_number=MAX_ATTEMPTS, wait_fixed=DELAY)
    def get_balance(self, asset):
        bal = self.client.get_asset_balance(asset=asset)
        return float(bal['free']), float(bal['locked'])

    @retry(stop_max_attempt_number=MAX_ATTEMPTS, wait_fixed=DELAY)
    def get_all_balances(self, assets: dict):
        res = self.client.get_account()

        if 'balances' in res:
            for bal in res['balances']:
                if bal['asset'] in assets:
                    assets[bal['asset']] = {'f': float(bal['free']), 'l':float(bal['locked'])}

    @retry(stop_max_attempt_number=MAX_ATTEMPTS, wait_fixed=DELAY)
    def get_exchange_info(self, sym):
        info = self.client.get_exchange_info()

        symbol_info = None
        for s in info['symbols']:
            if s['symbol'] == sym:
                symbol_info = s
                break

        props = {}
        for f in symbol_info['filters']:
            props.update(f)

        props.pop('filterType', None)

        return FXConnector.ExchangeInfo(**props)

    @classmethod
    def format_number(cls, num):
        return '{:.08f}'.format(num)
