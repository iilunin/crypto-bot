import traceback
from datetime import datetime as dt
from threading import RLock
from typing import List

from Bot.AccountBalances import AccountBalances
from Bot.ExchangeInfo import ExchangeInfo
from Bot.FXConnector import FXConnector
from Bot.Strategy.TargetsAndStopLossStrategy import TargetsAndStopLossStrategy
from Bot.Strategy.TradingStrategy import TradingStrategy
from Bot.Trade import Trade
from Utils.Logger import Logger


class TradeHandler(Logger):
    def __init__(self, trades: List[Trade], fx: FXConnector, trade_updated_handler=None):
        super().__init__()
        self.fx = fx
        self.balances = AccountBalances()

        self.order_updated_handler = trade_updated_handler
        ExchangeInfo().update(fx.get_exchange_info())
        self.strategies = []

        self.logInfo('Creating {} with {} trades.'.format(self.__class__.__name__, len(trades)))

        for t in trades:
            try:
                if t.symbol not in ExchangeInfo().symbols:
                    self.logError('Exchange doesn\'t have market "{}"'.format(t.symbol))
                    continue

                self.strategies.append(
                    TargetsAndStopLossStrategy(t, fx, trade_updated_handler, self.balances.get_balance(t.asset)))
            except Exception:
                self.logError(traceback.format_exc())

        self.strategies_dict = {}
        self.tradeid_strategy_dict = {}
        self.trade_info_ticker_buf = {}

        self.process_delay = 500
        self.last_ts = dt.now()
        self.first_processing = True
        self.socket_message_rcvd = False
        self.paused = False

        self.lock = RLock()

    def pause(self):
        self.logInfo('Pausing trade handler')
        self.paused = True

    def resume(self):
        self.logInfo('Resuming trade handler')
        self.paused = False

    def process_initial_prices(self):
        try:
            if not self.first_processing:
                return

            self.first_processing = False

            tickers = self.fx.get_orderbook_tickers()
            # tickers = self.fx.get_all_tickers()
            # prices = {t['symbol']: float(t['price']) for t in tickers}

            prices = {t['symbol']: {'b': float(t['bidPrice']), 'a': float(t['askPrice'])} for t in tickers}
            self.execute_strategies(prices)
        except Exception:
            self.logError(traceback.format_exc())

    def start_listening(self):
        # self.init_trades()
        self.fx.start_listening()
        self.last_ts = dt.now()

    def remove_strategy(self, strategy: TradingStrategy):
        if strategy in self.strategies:
            self.strategies.remove(strategy)

        sym = strategy.symbol()
        if sym in self.strategies_dict:
            if len(self.strategies_dict[sym]) > 1:
                self.strategies_dict.remove(strategy)
            else:
                self.strategies_dict.pop(sym, None)

        if strategy.trade.id in self.tradeid_strategy_dict:
            self.tradeid_strategy_dict.pop(strategy.trade.id, None)

        self.fx.listen_symbols([s.symbol() for s in self.strategies], self.listen_handler, self.user_data_handler)
        self.socket_message_rcvd = False

    def add_new_strategy(self, strategy: TradingStrategy):
        self.strategies.append(strategy)

        sym = strategy.symbol()
        if sym in self.strategies_dict:
            self.strategies_dict[sym].append(strategy)
        else:
            self.strategies_dict[sym] = [strategy]

        self.tradeid_strategy_dict[strategy.trade.id] = strategy

        # self.balances.update_balances(self.fx.get_all_balances_dict())

        if not ExchangeInfo().has_all_symbol(self.strategies_dict.keys()):
            ExchangeInfo().update(self.fx.get_exchange_info())

        self.fx.listen_symbols([s.symbol() for s in self.strategies], self.listen_handler, self.user_data_handler)
        self.socket_message_rcvd = False

    def init_strategies(self):
        # self.strategies_dict = {s.symbol(): s for s in self.strategies}
        self.strategies_dict = {}
        for strategy in self.strategies:
            sym = strategy.symbol()

            if sym in self.strategies_dict:
                self.strategies_dict[sym].append(strategy)
            else:
                self.strategies_dict[sym] = [strategy]

        self.tradeid_strategy_dict = {s.trade.id: s for s in self.strategies}

        self.balances.update_balances(self.fx.get_all_balances_dict())

        if not ExchangeInfo().has_all_symbol(self.strategies_dict.keys()):
            ExchangeInfo().update(self.fx.get_exchange_info())

        self.process_initial_prices()
        self.fx.listen_symbols([s.symbol() for s in self.strategies], self.listen_handler, self.user_data_handler)
        self.socket_message_rcvd = False

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
                    for s in self.strategies_dict[sym]:
                        s.on_execution_rpt(
                            {'orderId': msg['i'],
                             'status': msg['X'],
                             'symbol': sym,
                             'side': msg['S'],
                             'vol': msg['q'],
                             'price': msg['p'],
                             'stop_price': msg['P']})
                    # self.strategies_dict[sym].on_execution_rpt(
                    #     {'orderId': msg['i'],
                    #      'status': msg['X'],
                    #      'symbol': sym,
                    #      'side': msg['S'],
                    #      'vol': msg['q'],
                    #      'price': msg['p'],
                    #      'stop_price': msg['P']})
        except Exception as e:
            self.logError(traceback.format_exc())
            # self.logger.error(str(e))

    def listen_handler(self, msg):
        try:
            if self.paused:
                return

            if not self.socket_message_rcvd:
                self.confirm_socket_msg_rcvd()

            delta = dt.now() - self.last_ts
            if isinstance(msg, list):
                for ticker in msg:
                    if ticker['s'] in self.strategies_dict and ticker['e'] == '24hrTicker':
                        self.trade_info_ticker_buf[ticker['s']] = {'b': float(ticker['b']), 'a': float(ticker['a'])}
            else:
                d = msg['data']

                if 'error' in (msg.get('e', None), d.get('e', None)):
                    self.logError(msg)
                    return
                elif d['e'] == '24hrTicker':
                    self.trade_info_ticker_buf[d['s']] = {'b': float(d['b']), 'a': float(d['a'])}
                    # delta = dt.now() - self.last_ts

            if (delta.seconds * 1000 + (delta).microseconds / 1000) > self.process_delay:
                self.last_ts = dt.now()
                self.check_strategies_status()
                prices = dict(self.trade_info_ticker_buf)
                self.trade_info_ticker_buf = {}
                self.execute_strategies(prices)

        except Exception as e:
            self.logError(traceback.print_exc())

    def execute_strategies(self, prices):
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
            self.logInfo('Removing trade [{}]'.format(strategy.symbol()))
            try:
                self.stop_listening()
                self.remove_strategy(strategy)
            finally:
                self.start_listening()

    # def remove_trade_by_symbol(self, sym):
    #     with self.lock:
    #         self.remove_trade_by_strategy(self.strategies_dict.get(sym, None))

    def remove_trade_by_id(self, id):
        with self.lock:
            self.remove_trade_by_strategy(self.tradeid_strategy_dict.get(id, None))

    def updated_trade(self, trade: Trade):
        with self.lock:
            if trade.id in self.tradeid_strategy_dict:
                # find by ID
                # self.strategies_dict[trade.symbol].update_trade(trade)
                self.tradeid_strategy_dict[trade.id].update_trade(trade)

                if self.handle_completed_strategy(self.tradeid_strategy_dict[trade.id]):
                    self.logInfo('Strategy is completed [{}]'.format(trade.symbol))
                    return

                self.balances.update_balances(self.fx.get_all_balances_dict())
                self.logInfo('Updating trade [{}]'.format(trade.symbol))
            else:
                self.logInfo('Adding trade [{}]'.format(trade.symbol))

                new_strategy = TargetsAndStopLossStrategy(trade, self.fx, self.order_updated_handler,
                                                      self.balances.get_balance(trade.asset))

                if self.handle_completed_strategy(new_strategy):
                    self.logInfo('Strategy is completed [{}]'.format(new_strategy.symbol()))
                    return

                try:
                    self.stop_listening()
                    self.add_new_strategy(new_strategy)
                finally:
                    self.start_listening()

    def confirm_socket_msg_rcvd(self):
        self.socket_message_rcvd = True
        self.logInfo('WebSocket message received')
