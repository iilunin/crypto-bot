import traceback
from threading import Lock, RLock
from typing import List
import numpy as np
from datetime import datetime as dt

import logging

from Bot.AccountBalances import AccountBalances
from Bot.FXConnector import FXConnector
from Bot.Trade import Trade
from Bot.Strategy.TargetsAndStopLossStrategy import TargetsAndStopLossStrategy


class TradeHandler:
    def __init__(self, trades: List[Trade], fx: FXConnector, order_updated_handler=None):
        self.fx = fx
        self.balances = AccountBalances()

        self.order_updated_handler = order_updated_handler
        self.strategies = [TargetsAndStopLossStrategy(t, fx, order_updated_handler, self.balances.get_balance(t.asset))
                           for t in trades]

        self.strategies_dict = {}
        self.asset_dict = {}
        self.trade_info_buf = {}
        self.trade_info_ticker_buf = {}

        self.process_delay = 500
        self.last_ts = dt.now()
        self.first_processing = True

        self.logger = logging.getLogger('OrderHandler')
        self.lock = RLock()

    def process_initial_prices(self):
        try:
            if not self.first_processing:
                return

            self.first_processing = False

            tickers = self.fx.get_orderbook_tickers()
            # tickers = self.fx.get_all_tickers()
            # prices = {t['symbol']: float(t['price']) for t in tickers}

            prices = {t['symbol']: {'b': float(t['bidPrice']), 'a': float(t['askPrice'])} for t in tickers}
            self.execute_strategy(prices)
        except Exception as e:
            self.logger.error(traceback.format_exc())


    def start_listening(self):
        self.strategies_dict = {s.symbol(): s for s in self.strategies}
        self.asset_dict = {s.trade.asset: s for s in self.strategies}
        self.trade_info_buf = {s.symbol(): [] for s in self.strategies}

        self.balances.update_balances(self.fx.get_all_balances_dict())

        # balances = dict.fromkeys(self.asset_dict.keys())
        # self.fx.get_all_balances(balances)

        # [s.update_asset_balance(balances[s.trade.asset]['f'], balances[s.trade.asset]['l']) for s in self.strategies]


        self.process_initial_prices()

        self.fx.listen_symbols([s.symbol() for s in self.strategies], self.listen_handler, self.user_data_handler)
        self.fx.start_listening()

        self.last_ts = dt.now()


    def stop_listening(self):
        self.fx.stop_listening()

    def user_data_handler(self, msg):
        try:
            if msg['e'] == 'outboundAccountInfo':
                self.balances.update_balances(
                    {bal['a']: {'f': float(bal['f']), 'l': float(bal['l'])} for bal in msg['B']})
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
            self.logger.error(traceback.format_exc())
            # self.logger.error(str(e))

    def listen_handler(self, msg):
        try:
            d = msg['data']
            if 'error' in (msg.get('e', None), d.get('e', None)):
                self.logger.error(msg)
            # elif d['e'] == 'trade':
            #     self.trade_info_buf[d['s']].append(d['p'])
            #     delta = dt.now() - self.last_ts
            #     if (delta.seconds * 1000 + (delta).microseconds / 1000) > self.process_delay:
            #         self.last_ts = dt.now()
            #         mean_prices = self.aggreagate_fx_prices()
            #         self.check_strategy_is_complete()
            #         self.execute_strategy(mean_prices)
            elif d['e'] == '24hrTicker':
                self.trade_info_ticker_buf[d['s']] = {'b': float(d['b']), 'a': float(d['a'])}

                delta = dt.now() - self.last_ts

                if (delta.seconds * 1000 + (delta).microseconds / 1000) > self.process_delay:
                    self.last_ts = dt.now()
                    self.check_strategies_status()
                    prices = dict(self.trade_info_ticker_buf)
                    self.trade_info_ticker_buf = {}
                    self.execute_strategy(prices)

        except Exception as e:
            self.logger.error(str(e))
            traceback.print_exc()


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
        with self.lock:
            for s in self.strategies:
                if s.symbol() in prices:
                    s.execute(prices[s.symbol()])

    def check_strategies_status(self):
        for s in self.strategies[:]:
            self.handle_completed_strategy(s)

    def handle_completed_strategy(self, s):
        if s.is_completed():
            self.remove_trade_by_strategy(s)
        return s.is_completed()

    def remove_trade_by_strategy(self, strategy):
        if not strategy:
            return

        with self.lock:
            self.logger.info('Removing trade [{}]'.format(strategy.symbol()))
            self.stop_listening()
            self.strategies.remove(strategy)
            self.start_listening()

    def remove_trade_by_symbol(self, sym):
        with self.lock:
            self.remove_trade_by_strategy(self.strategies_dict.get(sym, None))

    def updated_trade(self, trade: Trade):
        with self.lock:
            if trade.symbol in self.strategies_dict:
                self.strategies_dict[trade.symbol].update_trade(trade)
                self.balances.update_balances(self.fx.get_all_balances_dict())
                self.logger.info('Updating trade [{}]'.format(trade.symbol))
            else:
                self.logger.info('Adding trade [{}]'.format(trade.symbol))
                self.stop_listening()
                self.strategies.append(TargetsAndStopLossStrategy(trade, self.fx, self.order_updated_handler, self.balances.get_balance(trade.asset)))
                self.start_listening()
