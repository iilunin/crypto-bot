from binance.exceptions import BinanceAPIException, BinanceOrderException
from retrying import retry

from binance.client import Client
from Bot.Exchange.Binance.BinanceWebsocket import BinanceWebsocket
from Utils.Logger import Logger

MAX_ATTEMPTS = 3
DELAY = 1000

def retry_on_exception(exc):
    return isinstance(exc, (BinanceAPIException, BinanceOrderException))

DEFAULT_RETRY_SETTINGS = {
    'stop_max_attempt_number': MAX_ATTEMPTS,
    'wait_fixed': DELAY,
    'retry_on_exception': retry_on_exception
}

class FXConnector(Logger):
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
        super().__init__()
        self.__key = key
        self.__secret = secret
        self._client = None #Client(key, secret)
        self.bs: BinanceWebsocket = None

        # self.connection = None
        self.ticker_connection = None
        self.user_data_connection = None

    @property
    def client(self):
        if not self._client:
            self._client = Client(self.__key, self.__secret)

        return self._client

    def listen_symbols(self, symbols, on_ticker_received, user_data_handler):
        self.bs = BinanceWebsocket(self.client)
        self.bs.start_ticker(symbols, on_ticker_received)
        self.bs.start_user_info(user_data_handler)

        self.logInfo('Ticker and User WS initialized')

    def start_listening(self):
        self.bs.start()
        self.logInfo('WS listening started')

    def stop_listening(self):
        if self.bs:
            self.bs.stop_sockets()
            self.logInfo('Socket stopped')

    @retry(**DEFAULT_RETRY_SETTINGS)
    def cancel_order(self, sym, id):
        '''
        :param sym:
        :param id:
        :return:
        {
            'symbol': 'ETCUSDT',
            'origClientOrderId': 'asd',
            'orderId': 1211742179,
            'orderListId': -1,
            'clientOrderId': 'xyz',
            'price': '100.00000000',
            'origQty': '5.00000000',
            'executedQty': '0.00000000',
            'cummulativeQuoteQty': '0.00000000',
            'status': 'CANCELED',
            'timeInForce': 'GTC',
            'type': 'LIMIT',
            'side': 'SELL'}
        '''
        return self.client.cancel_order(symbol=sym, orderId=id)

    @retry(**DEFAULT_RETRY_SETTINGS)
    def cancel_open_orders(self, sym):
        orders = self.get_open_orders(sym)
        if orders:
            for order_id in orders:
                self.client.cancel_order(symbol=sym, orderId=order_id)

    @retry(**DEFAULT_RETRY_SETTINGS)
    def cancel_open_orders_direct_api(self, sym):
        return self.client._delete('openOrders', True, data={'symbol': sym})
        # self.client.cancel_open
        # orders = self.get_open_orders(sym)
        # if orders:
        #     for order_id in orders:
        #         self.client.cancel_order(symbol=sym, orderId=order_id)

    def get_server_time(self):
        return self.client.get_server_time()

    @retry(**DEFAULT_RETRY_SETTINGS)
    def get_open_orders(self, sym):
        return [o['orderId'] for o in self.client.get_open_orders(symbol=sym)]

    @retry(**DEFAULT_RETRY_SETTINGS)
    def get_all_orders(self, sym, limit=500):
        return {o['orderId']: {'status': o['status'],
                               'price': o['price'],
                               'stop_price': o['stopPrice'],
                               'vol': o['origQty'],
                               'vol_exec': o['executedQty']}
                for o in self.client.get_all_orders(symbol=sym, limit=limit)}

    @retry(**DEFAULT_RETRY_SETTINGS)
    def get_all_tickers(self):
        return self.client.get_all_tickers()

    @retry(**DEFAULT_RETRY_SETTINGS)
    def get_orderbook_tickers(self, sym):
        if sym:
            return self.client._get('ticker/bookTicker', version=self.client.PRIVATE_API_VERSION, data={'symbol':sym})
        return self.client.get_orderbook_tickers()

    @retry(**DEFAULT_RETRY_SETTINGS)
    def get_order_status(self, sym, id):
        return self.client.get_order(symbol=sym, orderId=id)

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

    @retry(**DEFAULT_RETRY_SETTINGS)
    def get_balance(self, asset):
        bal = self.client.get_asset_balance(asset=asset)
        return float(bal['free']), float(bal['locked'])

    @retry(**DEFAULT_RETRY_SETTINGS)
    def get_all_balances(self, assets: dict):
        res = self.client.get_account()

        if 'balances' in res:
            for bal in res['balances']:
                if bal['asset'] in assets:
                    assets[bal['asset']] = {'f': float(bal['free']), 'l': float(bal['locked'])}

    @retry(**DEFAULT_RETRY_SETTINGS)
    def get_all_balances_dict(self):
        res = self.client.get_account()

        if 'balances' in res:
            return {bal['asset']: {'f': float(bal['free']), 'l': float(bal['locked'])} for bal in res['balances']}

        return {}

    @retry(**DEFAULT_RETRY_SETTINGS)
    def get_exchange_info(self):
        return self.client.get_exchange_info()
        # info = self.client.get_exchange_info()
        #
        # symbol_info = None
        # for s in info['symbols']:
        #     if s['symbol'] == sym:
        #         symbol_info = s
        #         break
        #
        # props = {}
        # for f in symbol_info['filters']:
        #     props.update(f)
        #
        # props.pop('filterType', None)
        #
        # return FXConnector.ExchangeInfo(**props)

    @classmethod
    def format_number(cls, num):
        return '{:.08f}'.format(num)
