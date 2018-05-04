import logging
import os
import shutil
import traceback
from datetime import datetime
from threading import Timer, Lock, RLock

from os.path import isfile, join

from os import listdir, environ

from Bot import Trade
from Bot.ConfigLoader import ConfigLoader
from Bot.FXConnector import FXConnector
from Bot.TradeHandler import TradeHandler
from Bot.TradeValidator import TradeValidator
from Cloud.S3Sync import S3Persistence
from Utils.Logger import Logger
from Utils import Utils


class ConsoleLauncher(Logger):
    TRADE_FILE_PATH_PATTERN = '{path}{time}{symbol}.json'

    def __init__(self, trades_path, completed_trades_path, config_path, enable_cloud=False):
        super().__init__()
        self.trades_path = trades_path
        self.completed_trades_path = completed_trades_path
        self.config_path = config_path

        self.config_loader = ConfigLoader()

        self.trade_handler: TradeHandler = None
        self.fx = None

        self.file_watch_list = {}
        self.file_watch_timer = None
        self.lock = RLock()

        self.enable_cloud = enable_cloud
        self.s3pers: S3Persistence = None

        if enable_cloud:
            self.s3pers: S3Persistence = S3Persistence(os.getenv('TRADE_BUCKET'), {trades_path: 'Portfolio/', completed_trades_path: 'Completed/'})

    def start_bot(self):
        self.sync_down()

        # trade_loader = self.config_loader.advanced_loader(self.trades_path)
        trades = self.config_loader.load_trade_list(self.trades_path)
        trade_validator = TradeValidator()

        self.logInfo('Starting Bot...')

        for trade in trades[:]:
            if trade.is_completed():
                self.move_completed_trade(trade)
            if not trade_validator.validate(trade):
                self.logError('{}:{}'.format(trade.symbol, trade_validator.errors))
                if len(trade_validator.warnings) > 0:
                    self.logInfo('{}:{}'.format(trade.symbol, trade_validator.warnings))
                trades.remove(trade)

        api_path = os.path.join(self.config_path, 'api.json')
        key, secret = self.get_exchange_creds(api_path)

        self.fx = FXConnector(key, secret)

        self.trade_handler = TradeHandler(
            trades,
            self.fx,
            lambda trade, cloud_sync: self.on_trade_updated_by_handler(trade, cloud_sync)
        )

        self.init_file_watch_list()
        self.start_timer()

        self.trade_handler.init_strategies()
        self.trade_handler.start_listening()

    def get_exchange_creds(self, api_path):
        if os.environ.get('KEY') and os.environ.get('SECRET'):
            key = os.environ.get('KEY')
            secret = os.environ.get('SECRET')
        elif os.path.exists(api_path):
            api = self.config_loader.json_loader(os.path.join(self.config_path, 'api.json'))()
            exchanges = [ex for ex in api['exchanges'] if ex['name'].lower() == 'binance']

            if len(exchanges) > 0:
                api = exchanges[0]

            key = api['key']
            secret = api['secret']

        if not key or not secret:
            raise ValueError('API Key and Secret are not provided')
        return key, secret

    def sync_down(self):
        if self.enable_cloud:
            self.s3pers.sync(False, True)
            self.s3pers.await()

    def init_file_watch_list(self):
        target_path_list = [f for f in listdir(self.trades_path) if
                            isfile(join(self.trades_path, f)) and f.lower().endswith('json')]

        for trade_path in target_path_list:
            file = join(self.trades_path, trade_path)

            self.file_watch_list[file] = os.stat(file).st_mtime

    def stop_bot(self):
        if self.trade_handler:
            self.trade_handler.stop_listening()
        self.stop_timer()

    def start_timer(self):
        self.file_watch_timer = Timer(5, self.check_files_changed)
        self.file_watch_timer.name = 'Filewatch Timer'
        self.file_watch_timer.start()

    def stop_timer(self):
        if self.file_watch_timer:
            self.file_watch_timer.cancel()
            self.file_watch_timer = None

    def check_files_changed(self):
        try:
            deleted_by_s3, updated_by_s3 = set(), set()
            if self.enable_cloud:
                deleted_by_s3, updated_by_s3 = self.s3pers.check_s3_events()

            with self.lock:
                target_path_dict = {join(self.trades_path, f): os.stat(join(self.trades_path, f)).st_mtime for f in
                                    listdir(self.trades_path) if
                                    isfile(join(self.trades_path, f)) and f.lower().endswith('json')}

            removed_files = set(self.file_watch_list.keys()) - set(target_path_dict.keys())

            update_cloud_files = False

            if removed_files:
                for file in removed_files:
                    sym, trade_id = Utils.get_symbol_and_id_from_file_path(file)

                    if trade_id:
                        self.trade_handler.remove_trade_by_id(trade_id)
                    else:
                        self.logError('Can\'t remove trade {}'.format(file))
                    # else:
                    #     self.trade_handler.remove_trade_by_symbol(sym)

                    self.file_watch_list.pop(file, None)

                if file not in deleted_by_s3:
                    update_cloud_files = True

            for file, current_mtime in target_path_dict.items():
                if file in self.file_watch_list:
                    if not self.file_watch_list[file] == current_mtime:
                        self.logInfo('File "{}" has changed. Updating trades...'.format(file))
                        trades = self.config_loader.load_trade_list(file)
                        for t in trades:
                            self.trade_handler.updated_trade(t)

                        if file not in updated_by_s3:
                            update_cloud_files = True

                    self.file_watch_list[file] = os.stat(file).st_mtime

                else:
                    self.logInfo('New file detected "{}". Updating trades...'.format(file))
                    update_cloud_files = True
                    trades = self.config_loader.load_trade_list(file)
                    for t in trades:
                        #if file needs to be adjusted to the new format
                        new_file_name = os.path.join(self.trades_path, Utils.get_file_name(t))
                        if new_file_name != file:
                            self.file_watch_list[new_file_name] = os.stat(new_file_name).st_mtime
                            self.file_watch_list.pop(file, None)
                        else:
                            if os.path.exists(file):
                                self.file_watch_list[file] = os.stat(file).st_mtime

                        self.trade_handler.updated_trade(t)

                    if file not in updated_by_s3:
                        update_cloud_files = True

            if update_cloud_files and self.enable_cloud:
                self.s3pers.sync(True, True)

        except Exception as e:
            self.logError(traceback.format_exc())
        finally:
            self.start_timer()

    def on_trade_updated_by_handler(self, trade: Trade, needs_cloud_sync=True):
        with self.lock:
            file = self.get_file_path(self.trades_path, trade)

            self.config_loader.persist_updated_trade(trade, self.config_loader.json_saver(file))

            self.file_watch_list[file] = os.stat(file).st_mtime

            if trade.is_completed():
                self.move_completed_trade(trade)

            if self.enable_cloud and needs_cloud_sync:
                self.s3pers.sync(True, True)

    def move_completed_trade(self, trade):
        shutil.move(self.get_file_path(self.trades_path, trade),
                  self.get_file_path(self.completed_trades_path, trade, datetime.now().strftime('%Y-%m-%d_%H-%M-')))

    def get_file_path(self, path, trade, time=''):
        return os.path.join(path, '{time}{fn}'.format(fn=Utils.get_file_name(trade), time=time))
