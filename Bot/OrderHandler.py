from typing import List
import numpy as np
from datetime import datetime as dt

from Bot.FXConnector import FXConnector
from Bot.Order import Order
from Bot.OrderStrategy import TargetsAndStopLossStrategy


class OrderHandler:
    def __init__(self, orders: List[Order], fx: FXConnector):
        # self.orders = {o.symbol: o for o in orders}
        self.fx = fx

        self.strategies = [TargetsAndStopLossStrategy(o, fx) for o in orders]

        self.trade_info_buf = {}
        self.trend = {}
        self.process_delay = 500
        self.last_ts = 0

    def start_listening(self):
        self.fx.listen_symbols([s.symbol() for s in self.strategies], self.listen_handler, self.user_data_handler)

        self.trade_info_buf.clear()
        self.trade_info_buf = {s.symbol(): [] for s in self.strategies}
        self.trend = {s.symbol(): [] for s in self.strategies}

        self.validate_assets()

        self.fx.start_listening()
        self.last_ts = dt.now()


    def stop_listening(self):
        self.fx.stop_listening()

    def user_data_handler(self, msg):
        if msg['e'] == 'outboundAccountInfo':
            pass
        elif msg['e'] == 'executionReport':
            pass
        print(msg)

    def listen_handler(self, msg):
        # {
        #     "e": "trade",  # Event type
        #     "E": 123456789,  # Event time
        #     "s": "BNBBTC",  # Symbol
        #     "t": 12345,  # Trade ID
        #     "p": "0.001",  # Price
        #     "q": "100",  # Quantity
        #     "b": 88,  # Buyer order Id
        #     "a": 50,  # Seller order Id
        #     "T": 123456785,  # Trade time
        #     "m": true,  # Is the buyer the market maker?
        #     "M": true  # Ignore.
        # }
        d = msg['data']
        if d['e'] == 'error':
            print(msg['data'])
        else:
            self.trade_info_buf[d['s']].append(d['p'])
            delta = dt.now() - self.last_ts
            if (delta.seconds * 1000 + (delta).microseconds / 1000) > self.process_delay:
                self.last_ts = dt.now()
                mean_prices = self.aggreagate_fx_prices()
                self.execute_strategy(mean_prices)


    def aggreagate_fx_prices(self):
        mp = {}
        for sym, prices in self.trade_info_buf.items():
            if not prices:
                continue
            mean_price = np.mean(np.array(prices).astype(np.float))
            print('{}:{:.8f}; {}'.format(sym, mean_price, len(prices)))
            self.trade_info_buf[sym] = []

            mp[sym] = mean_price

        return mp

    def execute_strategy(self, prices):
        for s in self.strategies:
            if s.symbol() in prices:
                s.execute(prices[s.symbol()])

    def validate_assets(self):
        [s.validate_asset_size() for s in self.strategies]
