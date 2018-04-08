import logging

from binance.exceptions import BinanceAPIException

from Bot.FXConnector import FXConnector
from Bot.TradeEnums import OrderStatus
from Bot.Target import Target, PriceHelper
from Bot.Trade import Trade


class Balance:
    def __init__(self, available=0., locked=0.):
        self.avail = available
        self.locked = locked


class TradingStrategy:
    def __init__(self, trade: Trade, fx: FXConnector, order_updated=None, nested=False, exchange_info=None, balance=None):
        self.trade = trade
        self.fx = fx
        self.balance = Balance()
        self.exchange_info = None
        self.simulate = False
        self.trade_updated = order_updated
        self.name = '{}({})'.format(self.__class__.__name__, self.symbol())
        self.logger = logging.getLogger(self.name)

        if nested:
            self.exchange_info = exchange_info

            if balance:
                self.balance = balance
        else:
            self.init()

    def init(self):
        self.exchange_info = self.fx.get_exchange_info(self.symbol())
        self.validate_target_orders()

    def is_completed(self):
        return self.trade.is_completed()

    def trade_side(self):
        return self.trade.side

    def symbol(self):
        return self.trade.symbol

    def execution_rpt(self, data):
        self.logInfo('Execution Rpt: {}'.format(data))
        orderId = data['orderId']

        tgts = self.trade.get_all_active_placed_targets()

        for t in tgts:
            if t.id == orderId:
                if self._update_trade_target_status_change(t, data['status']):
                    self.trigger_target_updated()
                    self.order_status_changed(t, data)
                break

    def order_status_changed(self, t: Target, data):
        pass

    def account_info(self, data):
        self.balance.avail = float(data['f'])
        self.balance.locked = float(data['l'])

    # TODO: schedule validation once in some time
    def validate_target_orders(self):
        try:
            orders_dict = self.fx.get_all_orders(self.symbol())
        except BinanceAPIException as bae:
            self.logError(str(bae))
            return

        tgts = self.trade.get_all_active_placed_targets()

        update_required = False
        for t in tgts:
            if t.id not in orders_dict:
                t.set_canceled()
                update_required = True
            else:
                s = orders_dict[t.id]['status']
                if s == 'NEW':
                    if not PriceHelper.is_float_price(t.price) or (
                            self.exchange_info.adjust_price(t.price) not in(float(orders_dict[t.id]['price']),
                                                                       float(orders_dict[t.id]['stop_price']))):
                        self.logInfo('Target price changed: {}'.format(t))
                        self.fx.cancel_order(self.symbol(), t.id)
                        t.set_canceled()

                update_required |= self._update_trade_target_status_change(t, s)

        if update_required:
            self.trigger_target_updated()

    def _update_trade_target_status_change(self, t: Target, status: str) -> bool:
        if status == 'FILLED':
            t.set_completed()
            return True

        if status in ['CANCELED', 'REJECTED', 'EXPIRED']:
            t.set_canceled()
            return True

        return False


    def execute(self, new_price):
        pass

    def update_asset_balance(self, avail, locked):
        self.balance.avail = avail
        self.balance.locked = locked

    def validate_asset_balance(self):
        self.balance.avail, self.balance.locked = self.fx.get_balance(self.trade.asset)

    def set_trade_completed(self):
        self.trade.status = OrderStatus.COMPLETED
        self.trigger_target_updated()

    def trigger_target_updated(self):
        if self.trade_updated:
            self.trade_updated(self.trade)

    #TODO: move logging to another class
    def logInfo(self, msg):
        self.logger.log(logging.INFO, msg)

    def logWarning(self, msg):
        self.logger.log(logging.WARNING, msg)

    def logError(self, msg):
        self.logger.log(logging.ERROR, msg)
