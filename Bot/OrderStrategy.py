import logging

from binance.exceptions import BinanceAPIException

from Bot import StopLossSettings
from Bot.FXConnector import FXConnector
from Bot.Trade import Trade
from Bot.OrderStatus import OrderStatus
from Bot.StopLossSettings import StopLossSettings
from Bot.Value import Value

class OrderStrategy:
    def __init__(self, trade: Trade, fx: FXConnector, order_updated=None):
        self.trade = trade
        self.fx = fx
        self.available = 0.
        self.locked = 0.
        self.exchange_info = None
        self.simulate = False
        self.trade_updated = order_updated
        self.logger = logging.getLogger('{}({})'.format(self.__class__.__name__, self.symbol()))
        self.init()

    def init(self):
        self.exchange_info = self.fx.get_exchange_info(self.symbol())
        self.validate_target_orders()

    def logInfo(self, msg):
        self.logger.log(logging.INFO, msg)

    def logError(self, msg):
        self.logger.log(logging.ERROR, msg)

    def symbol(self):
        return self.trade.symbol

    def validate_target_orders(self):
        orderIdList = self.fx.get_open_orders(self.symbol())
        tgts = self.trade.get_all_active_placed_targets()

        update_required = False
        for t in tgts:
            if t.id not in orderIdList:
                t.id = None
                update_required = True

        if update_required:
            self.trade_updated(self.trade)

    def execute(self, new_price):
        pass

    def validate_asset_balance(self):
        self.available, self.locked = self.fx.get_balance(self.trade.asset)


class TargetsAndStopLossStrategy(OrderStrategy):

    def __init__(self, trade: Trade, fx: FXConnector, order_updated=None):
        super().__init__(trade, fx, order_updated)
        self.current_stop_loss = 0
        self.adjust_stoploss_price()

    def execute(self, new_price):
        self.adjust_stoploss_price(new_price)
        self.adjust_stoploss_order(new_price)

        self.logInfo('SL:{:.08f}'.format(self.current_stop_loss))

    def adjust_stoploss_price(self, current_price=None):
        closed_targets = [o for o in self.trade.get_closed_targets()]
        has_closed_orders = len(closed_targets) > 0

        if has_closed_orders and closed_targets[-1].has_custom_stop():
            # sort by order value
            self.current_stop_loss = closed_targets[-1].sl
            return

        if current_price is None:
            self.current_stop_loss = self.trade.get_initial_stop().price
            return

        if not has_closed_orders:
            return

        expected_stop_loss = 0
        if self.trade.sl_settings.type == StopLossSettings.Type.TRAILING:

            trialing_val = self.trade.sl_settings.val

            if trialing_val.type == Value.Type.ABS:
                expected_stop_loss = current_price + (-1 if self.trade.is_sell_order() else 1) * trialing_val.v
            else:
                expected_stop_loss = current_price * (1 + (-1 if self.trade.is_sell_order() else 1) * trialing_val.v / 100)

            expected_stop_loss = round(expected_stop_loss, 8)
            if self.trade.is_sell_order() and expected_stop_loss > self.current_stop_loss:
                self.current_stop_loss = expected_stop_loss
            elif not self.trade.is_sell_order() and expected_stop_loss < self.current_stop_loss:
                self.current_stop_loss = expected_stop_loss

            self.logInfo('SL:{:.08f}, EXP:{:.08f}, P:{:.08f}'.format(self.current_stop_loss, expected_stop_loss, current_price))


    def adjust_stoploss_order(self, current_price):
        threshold = round(self.current_stop_loss * self.trade.sl_settings.threshold, 8)

        if (self.trade.is_sell_order() and (self.current_stop_loss + threshold) >= current_price) or \
            (not self.trade.is_sell_order() and (self.current_stop_loss - threshold) <= current_price):
            self.set_stoploss_order()
        else:
            self.cancel_stoploss_orders()

    def set_stoploss_order(self):
        # if we have order in place
        if self.trade.sl_settings.initial_target.id:
            self.logInfo('validating stoploss order')
            if True: # validate it
                return
            else:
                pass

        if self.simulate:
            order = self.fx.create_test_stop_order(self.symbol(), self.trade.side.name, self.current_stop_loss, 50)
            order['orderId'] = 2333123
        else:
            self.cancel_all_orders()
            self.validate_asset_balance()

            order = self.fx.create_stop_order(
                self.symbol(),
                self.trade.side.name,
                self.exchange_info.adjust_price(self.current_stop_loss),
                self.exchange_info.adjust_quanity(self.available)
            )

        self.trade.sl_settings.initial_target.id = order['orderId']
        self.trigger_order_updated()

        self.logInfo('setting stop loss order')

    def cancel_all_orders(self):
        self.logInfo('canceling all orders...')

        ids = self.fx.get_open_orders(self.symbol())
        active_targets = self.trade.get_all_active_placed_targets()

        for id in ids:
            self.fx.cancel_order(self.symbol(), id)
            self.logInfo('Order {} canceled'.format(id))
            try:
                tgt = next(t for t in active_targets if t.id == id)
                tgt.id = None
            except StopIteration:
                pass


    def cancel_stoploss_orders(self):
        if not self.trade.sl_settings.initial_target.id:
            return

        try:
            self.fx.cancel_order(self.symbol(), self.trade.sl_settings.initial_target.id)
        except BinanceAPIException as bae:
            self.logError(str(bae))

        self.trade.sl_settings.initial_target.id = None
        self.trigger_order_updated()
        self.logInfo('canceling stoploss orders')

    def trigger_order_updated(self):
        if self.trade_updated:
            self.trade_updated(self.trade)