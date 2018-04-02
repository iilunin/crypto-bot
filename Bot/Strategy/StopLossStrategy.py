import logging

from binance.exceptions import BinanceAPIException

from Bot.OrderStatus import OrderStatus
from Bot.StopLossSettings import StopLossSettings
from Bot.FXConnector import FXConnector
from Bot.Strategy.TradingStrategy import TradingStrategy
from Bot.Target import Target
from Bot.Trade import Trade
from Bot.Value import Value


class StopLossStrategy(TradingStrategy):
    def __init__(self, trade: Trade, fx: FXConnector, trade_updated=None, nested=False, exchange_info=None, balance=None):
        super().__init__(trade, fx, trade_updated, nested, exchange_info, balance)
        self.current_stop_loss = 0
        self.adjust_stoploss_price()

        if self.logger.isEnabledFor(logging.INFO):
            self.last_sl = 0
            self.last_th = 0

    def is_stoploss_order_active(self):
        return self.trade.get_initial_stop().is_active()

    def is_sl_completed(self):
        return self.trade.get_initial_stop().status == OrderStatus.COMPLETED

    def execute(self, new_price):

        if self.is_completed():
            return

        if self.is_sl_completed():
            return

        self.adjust_stoploss_price(new_price)
        self.adjust_stoploss_order(new_price)

        self.log_stoploss()

    def log_stoploss(self):
        if self.logger.isEnabledFor(logging.INFO):
            treshold = self.get_sl_treshold()
            if self.last_sl != self.current_stop_loss or self.last_th != treshold:
                self.logInfo('SL:{:.08f}. Will be placed if price drops to: {:.08f}'.format(self.current_stop_loss,
                                                                                            treshold))
                self.last_th = treshold
                self.last_sl = self.current_stop_loss

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
            self.validate_asset_balance()

    def get_sl_treshold(self):
        threshold = round(self.current_stop_loss * self.trade.sl_settings.threshold, 8)
        return (self.current_stop_loss + threshold) if self.trade.is_sell_order() else  (self.current_stop_loss - threshold)

    def order_status_changed(self, t: Target, data):
        if not t.is_stoploss_target():
            return

        if t.is_completed():
            self.set_trade_completed()
        else:
            self.logInfo('Order status updated: {}'.format(t.status))

    def set_stoploss_order(self):
        if self.trade.sl_settings.initial_target.is_active():
            return
            # self.logInfo('validating stoploss order')
            # if True: # validate it
            #     return
            # else:
            #     pass

        if self.simulate:
            order = self.fx.create_test_stop_order(self.symbol(), self.trade_side(), self.current_stop_loss, 50)
            order['orderId'] = 2333123
        else:
            self.cancel_all_orders()
            self.validate_asset_balance()

            # stop_trigger

            order = self.fx.create_stop_order(
                sym=self.symbol(),
                side=self.trade_side(),
                stop_price=self.exchange_info.adjust_price(self.current_stop_loss),
                price=self.exchange_info.adjust_price(self.get_sl_limit_price()),
                volume=self.exchange_info.adjust_quanity(self.balance.avail)
            )

        self.trade.sl_settings.initial_target.set_active(order['orderId'])
        self.trigger_target_updated()

        self.logInfo('setting stop loss order')

    def get_sl_limit_price(self):
        threshold = self.trade.sl_settings.limit_price_threshold

        if threshold.Type == Value.Type.ABS:
            return self.current_stop_loss + (-1 if self.is_sell_order() else 1) * self.trade.sl_settings.limit_price_threshold.v
        else:
            return self.current_stop_loss * (1 + (-1 if self.trade.is_sell_order() else 1) * threshold.v / 100)


    def cancel_all_orders(self):
        self.logInfo('canceling all orders...')

        ids = self.fx.get_open_orders(self.symbol())
        active_targets = self.trade.get_all_active_placed_targets()

        for id in ids:
            self.fx.cancel_order(self.symbol(), id)
            self.logInfo('Order {} canceled'.format(id))
            try:
                tgt = next(t for t in active_targets if t.id == id)
                tgt.set_canceled()
            except StopIteration:
                pass

    def cancel_stoploss_orders(self):
        if not self.trade.sl_settings.initial_target.id:
            return

        try:
            self.fx.cancel_order(self.symbol(), self.trade.sl_settings.initial_target.id)
        except BinanceAPIException as bae:
            self.logError(str(bae))

        self.trade.sl_settings.initial_target.set_canceled()
        self.trigger_target_updated()
        self.logInfo('canceling stoploss orders')
