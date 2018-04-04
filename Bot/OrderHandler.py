from typing import List
import numpy as np
from datetime import datetime as dt

import logging

from Bot.FXConnector import FXConnector
from Bot.Trade import Trade
from Bot.Strategy.TargetsAndStopLossStrategy import TargetsAndStopLossStrategy


class OrderHandler:
    def __init__(self, trades: List[Trade], fx: FXConnector, order_updated_handler=None):
        # self.orders = {o.symbol: o for o in orders}
        self.fx = fx

        self.strategies = [TargetsAndStopLossStrategy(t, fx, order_updated_handler) for t in trades]
        self.strategies_dict = {}
        self.asset_dict = {}

        self.trade_info_buf = {}
        self.process_delay = 500
        self.last_ts = 0
        self.first_processing = True

        self.logger = logging.getLogger('OrderHandler')

    def process_initial_prices(self):
        try:
            if not self.first_processing:
                return

            self.first_processing = False

            tickers = self.fx.get_all_tickers()
            prices = {t['symbol']: float(t['price']) for t in tickers}
            self.execute_strategy(prices)
        except Exception as e:
            self.logger.error(str(e))


    def start_listening(self):
        self.process_initial_prices()

        self.strategies_dict = {s.symbol(): s for s in self.strategies}
        self.asset_dict = {s.trade.asset: s for s in self.strategies}

        self.fx.listen_symbols([s.symbol() for s in self.strategies], self.listen_handler, self.user_data_handler)

        self.trade_info_buf = {s.symbol(): [] for s in self.strategies}

        self.fx.start_listening()
        self.last_ts = dt.now()


    def stop_listening(self):
        self.fx.stop_listening()

    def user_data_handler(self, msg):
        try:
            if msg['e'] == 'outboundAccountInfo':
                assets = list(self.asset_dict.keys())
                for asset in msg['B']:
                    if asset['a'] in assets:
                        asset_name = asset['a']
                        strategy = self.asset_dict[asset_name]

                        strategy.account_info(asset)
                        assets.remove(asset_name)

                        if len(asset) == 0:
                            break
            elif msg['e'] == 'executionReport':
                sym = msg['s']

                if sym in self.strategies_dict:
                    self.strategies_dict[sym].execution_rpt(
                        {'orderId': msg['i'],
                         'status': msg['X'],
                         'symbol': sym,
                         'side': msg['S'],
                         'vol': msg['q'],
                         'price': msg['p'],
                         'stop_price': msg['P']})
        except Exception as e:
            self.logger.error(str(e))

    def listen_handler(self, msg):
        try:
            d = msg['data']
            if d['e'] == 'error':
                print(msg['data'])
            else:
                self.trade_info_buf[d['s']].append(d['p'])
                delta = dt.now() - self.last_ts
                if (delta.seconds * 1000 + (delta).microseconds / 1000) > self.process_delay:
                    self.last_ts = dt.now()
                    mean_prices = self.aggreagate_fx_prices()
                    self.check_strategy_is_complete()
                    self.execute_strategy(mean_prices)
        except Exception as e:
            self.logger.error(str(e))

    def aggreagate_fx_prices(self):
        mp = {}
        for sym, prices in self.trade_info_buf.items():
            if not prices:
                continue
            mean_price = np.mean(np.array(prices).astype(np.float))
            self.trade_info_buf[sym] = []

            mp[sym] = round(mean_price, 8)

        return mp

    def execute_strategy(self, prices):
        for s in self.strategies:
            if s.symbol() in prices:
                s.execute(prices[s.symbol()])

    def check_strategy_is_complete(self):
        for s in self.strategies[:]:
            if s.is_completed():
                self.strategies.remove(s)
                self.stop_listening()
                self.start_listening()
