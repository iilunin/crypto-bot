import logging
import os
import traceback
from datetime import datetime
from threading import Timer, Lock

from os.path import isfile, join

from os import listdir

from Bot import Trade
from Bot.ConfigLoader import ConfigLoader
from Bot.FXConnector import FXConnector
from Bot.OrderHandler import OrderHandler
from Bot.OrderValidator import OrderValidator


class ConsoleLauncher:
    TRADE_FILE_PATH_PATTERN = '{path}{time}{symbol}.json'

    LOG_FORMAT = '%(asctime)s[%(levelname)s][%(name)s]: %(message)s'
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

    def __init__(self, trades_path, completed_trades_path, config_path):
        self.trades_path = trades_path
        self.completed_trades_path = completed_trades_path
        self.config_path = config_path

        self.config_loader = ConfigLoader()

        self.logger = logging.getLogger(__class__.__name__)

        self.order_handler: OrderHandler = None
        self.fx = None

        self.file_watch_list = {}
        self.file_watch_timer = None
        self.lock = Lock()

    def start_bot(self):
        o_loader = self.config_loader.advanced_loader(self.trades_path)
        trades = self.config_loader.load_trade_list(o_loader)
        ov = OrderValidator()

        for trade in trades[:]:
            if trade.is_completed():
                self.move_completed_trade(trade.symbol)
            if not ov.validate(trade):
                self.logError('{}:{}'.format(trade.symbol, ov.errors))
                if len(ov.warnings) > 0:
                    self.logInfo('{}:{}'.format(trade.symbol, ov.warnings))
                trades.remove(trade)

        api = self.config_loader.json_loader(os.path.join(self.config_path, 'api.json'))()

        self.fx = FXConnector(api['key'], api['secret'])

        self.order_handler = OrderHandler(
            trades,
            self.fx,
            lambda trade: self.update_trade(trade)
        )

        self.init_file_watch_list()
        self.start_timer()
        self.order_handler.start_listening()
        xyz = 5

    def init_file_watch_list(self):
        target_path_list = [f for f in listdir(self.trades_path) if
                            isfile(join(self.trades_path, f)) and f.lower().endswith('json')]

        for trade_path in target_path_list:
            file = join(self.trades_path, trade_path)

            self.file_watch_list[file] = os.stat(file).st_mtime

    def stop_bot(self):
        if self.order_handler:
            self.order_handler.stop_listening()
        self.stop_timer()

    def start_timer(self):
        self.file_watch_timer = Timer(5, self.check_files_changed)
        self.file_watch_timer.start()

    def stop_timer(self):
        if self.file_watch_timer:
            self.file_watch_timer.cancel()
            self.file_watch_timer = None

    def check_files_changed(self):
        try:
            with self.lock:
                target_path_list = [f for f in listdir(self.trades_path) if
                                    isfile(join(self.trades_path, f)) and f.lower().endswith('json')]

            for trade_path in target_path_list:
                file = join(self.trades_path, trade_path)

                current_mtime = os.stat(file).st_mtime

                if file in self.file_watch_list:
                    if not self.file_watch_list[file] == current_mtime:
                        trades = self.config_loader.load_trade_list(self.config_loader.json_loader(file))
                        for t in trades:
                            self.order_handler.updated_trade(t)
                        self.logInfo('File "{}" has changed'.format(file))
                else:
                    self.logInfo('New file detected "{}"'.format(file))
                    trades = self.config_loader.load_trade_list(self.config_loader.json_loader(file))
                    for t in trades:
                        self.order_handler.updated_trade(t)

                self.file_watch_list[file] = os.stat(file).st_mtime
        except Exception as e:
            self.logError(traceback.format_exc())
        finally:
            self.start_timer()

    def update_trade(self, trade: Trade):
        with self.lock:
            file = self.get_file_path(self.trades_path, trade.symbol)

            self.config_loader.persist_updated_trade(trade,
                                                     self.config_loader.json_loader(file),
                                                     self.config_loader.json_saver(file))

            self.file_watch_list[file] = os.stat(file).st_mtime

            if trade.is_completed():
                self.move_completed_trade(trade.symbol)

    def move_completed_trade(self, symbol):
        os.rename(self.get_file_path(self.trades_path, symbol),
                  self.get_file_path(self.completed_trades_path, symbol, datetime.now().strftime('%Y-%m-%d_%H-%M-')))

    def get_file_path(self, path, symbol, time=''):
        return ConsoleLauncher.TRADE_FILE_PATH_PATTERN.format(path=path, symbol=symbol, time=time)

    def logInfo(self, msg):
        self.logger.info(msg)

    def logError(self, msg):
        self.logger.error(msg)
