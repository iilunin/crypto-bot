import logging

from binance.exceptions import BinanceAPIException

from Bot.AccountBalances import AccountBalances
from Bot.FXConnector import FXConnector
from Bot.Strategy.TradingStrategy import TradingStrategy
from Bot.Target import Target
from Bot.Trade import Trade


class StopLossStrategy(TradingStrategy):
    def __init__(self, trade: Trade, fx: FXConnector, trade_updated=None, nested=False, exchange_info=None, balance=None):
        super().__init__(trade, fx, trade_updated, nested, exchange_info, balance)
        self.current_stop_loss = 0
        self.exit_threshold = 0
        self.adjust_stoploss_price()

        # if self.logger.isEnabledFor(logging.INFO):
        self.last_sl = 0
        self.last_th = 0

    def update_trade(self, trade: Trade):
        self.trade = trade
        self.adjust_stoploss_price()

    def execute(self, new_price):
        if self.is_completed():
            return

        if self.is_sl_completed():
            return

        price = self.get_single_price(new_price)

        self.adjust_stoploss_price(price)
        self.adjust_stoploss_order(price)

        self.save_last_sl()
        self.log_stoploss()

    def save_last_sl(self):
        if self.last_sl != self.current_stop_loss and self.last_sl != 0:
            self.trade.sl_settings.last_stoploss = self.current_stop_loss
            self.trigger_target_updated()

    def is_stoploss_order_active(self):
        return self.initial_sl().is_active()

    def is_sl_completed(self):
        return self.initial_sl().is_completed()

    def is_completed(self):
        return self.is_sl_completed()

    def log_stoploss(self):
        treshold = self.get_sl_treshold()

        if self.last_sl != self.current_stop_loss or self.last_th != treshold:
            self.logInfo('{}SL:{:.08f}. Will be placed if price drops to: {:.08f}'.format(
                'TRAILING ' if self.trade.sl_settings.is_trailing() else '',
                self.current_stop_loss,
                treshold))
            self.last_th = treshold
            self.last_sl = self.current_stop_loss

    def adjust_stoploss_price(self, current_price=None):
        completed_targets = [o for o in self.trade.exit.get_completed_targets()]
        has_clopleted_targets = len(completed_targets) > 0

        if has_clopleted_targets and completed_targets[-1].has_custom_stop():
            # sort by order value
            self.current_stop_loss = completed_targets[-1].sl
            return

        if current_price is None:
            self.current_stop_loss = self.trade.sl_settings.last_stoploss if self.trade.sl_settings.last_stoploss != 0 \
                else self.initial_sl().price
            return

        if not has_clopleted_targets:
            return

        # expected_stop_loss = 0
        if self.trade.sl_settings.is_trailing():
            trialing_val = self.trade.sl_settings.val.get_val(current_price)
            expected_stop_loss = current_price + (-1 if self.trade.is_sell() else 1) * trialing_val

            expected_stop_loss = round(expected_stop_loss, 8)
            if self.trade.is_sell() and expected_stop_loss > self.current_stop_loss:
                self.current_stop_loss = expected_stop_loss
            elif not self.trade.is_sell() and expected_stop_loss < self.current_stop_loss:
                self.current_stop_loss = expected_stop_loss

            # if self.last_sl != self.current_stop_loss:
            #     self.logInfo('SL:{:.08f}, EXP:{:.08f}, P:{:.08f}'.format(self.current_stop_loss, expected_stop_loss, current_price))


    def adjust_stoploss_order(self, current_price):
        threshold = self.trade.sl_settings.zone_entry.get_val(self.current_stop_loss)

        if (self.trade.is_sell() and (self.current_stop_loss + threshold + self.exit_threshold) >= current_price) or \
            (not self.trade.is_sell() and (self.current_stop_loss - threshold - self.exit_threshold) <= current_price):
            self.set_stoploss_order()

            # if price bounce between placing and canceling order - additing small exit threshold
            if self.exit_threshold == 0:
                self.exit_threshold = threshold / 2
        else:
            self.exit_threshold = 0

            if self.cancel_stoploss_orders():
                AccountBalances().update_balances(self.fx.get_all_balances_dict())

    def get_sl_treshold(self):
        threshold = self.trade.sl_settings.zone_entry.get_val(self.current_stop_loss)
        return (self.current_stop_loss + threshold) if self.trade.is_sell() else (self.current_stop_loss - threshold)

    def on_order_status_changed(self, t: Target, data):
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

        try:
            if self.simulate:
                order = self.fx.create_test_stop_order(self.symbol(), self.trade_side().name, self.current_stop_loss, 50)
                order['orderId'] = 2333123
            else:
                self.cancel_all_orders()
                AccountBalances().update_balances(self.fx.get_all_balances_dict())

                price = self.exchange_info.adjust_price(self.get_sl_limit_price())
                bal = self.trade.get_cap(self.get_balance_for_side().avail)

                bal = round(bal / price, 8) if self.trade_side().is_buy() else bal

                volume = self.initial_sl().vol.get_val(bal)
                # stop_trigger
                try:
                    order = self.fx.create_stop_order(
                        sym=self.symbol(),
                        side=self.trade_side().name,
                        stop_price=self.exchange_info.adjust_price(self.current_stop_loss),
                        price=price,
                        volume=self.exchange_info.adjust_quanity(volume)
                    )
                except BinanceAPIException as sl_exception:
                    if sl_exception.message.lower().find('order would trigger immediately') > -1:
                        order = self.fx.create_makret_order(self.symbol(),
                                                            self.trade_side().name,
                                                            self.exchange_info.adjust_quanity(volume))
                    else:
                        raise

            self.trade.sl_settings.initial_target.set_active(order['orderId'])
            self.trigger_target_updated()
            self.logInfo('Setting stop loss order: {:.08f}:{:.08f}'.format(
                self.exchange_info.adjust_price(self.current_stop_loss),
                self.exchange_info.adjust_price(self.get_sl_limit_price())))
        except BinanceAPIException as bae:
            self.logError(str(bae))

    def initial_sl(self):
        return self.trade.get_initial_stop()

    def get_sl_limit_price(self):
        return self.current_stop_loss + (
            -1 if self.trade.is_sell() else 1) * self.trade.sl_settings.limit_price_threshold.get_val(
            self.current_stop_loss)


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
            return False

        try:
            self.fx.cancel_order(self.symbol(), self.trade.sl_settings.initial_target.id)
        except BinanceAPIException as bae:
            self.logError(str(bae))

        self.trade.sl_settings.initial_target.set_canceled()
        self.trigger_target_updated()
        self.logInfo('canceling stoploss orders')
        return True
