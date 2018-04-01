import logging

from Bot.FXConnector import FXConnector
from Bot.Trade import Trade


class TradingStrategy:
    def __init__(self, trade: Trade, fx: FXConnector, order_updated=None, nested=False, exchange_info=None):
        self.trade = trade
        self.fx = fx
        self.available = 0.
        self.locked = 0.
        self.exchange_info = None
        self.simulate = False
        self.trade_updated = order_updated
        self.name = '{}({})'.format(self.__class__.__name__, self.symbol())
        self.logger = logging.getLogger(self.name)

        if nested:
            self.exchange_info = exchange_info
        else:
            self.init()

    def init(self):
        self.exchange_info = self.fx.get_exchange_info(self.symbol())
        self.validate_target_orders()

    def is_completed(self):
        return self.trade.is_completed()

    def trade_side(self):
        return self.trade.side.name

    def symbol(self):
        return self.trade.symbol

    # TODO: schedule validation once in some time
    def validate_target_orders(self):
        orderIdList = self.fx.get_open_orders(self.symbol())
        tgts = self.trade.get_all_active_placed_targets()

        update_required = False
        for t in tgts:
            if t.id not in orderIdList:
                t.id = None
                update_required = True

        if update_required:
            self.trigger_order_updated()

    def execute(self, new_price):
        pass

    def validate_asset_balance(self):
        self.available, self.locked = self.fx.get_balance(self.trade.asset)

    def trigger_order_updated(self):
        if self.trade_updated:
            self.trade_updated(self.trade)

    #TODO: move logging to another class
    def logInfo(self, msg):
        self.logger.log(logging.INFO, msg)

    def logWarning(self, msg):
        self.logger.log(logging.WARNING, msg)

    def logError(self, msg):
        self.logger.log(logging.ERROR, msg)
