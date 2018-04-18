import traceback

from binance.exceptions import BinanceAPIException

from Bot.FXConnector import FXConnector
from Bot.Strategy.SmartOrder import SmartOrder
from Bot.Strategy.TradingStrategy import TradingStrategy
from Bot.Target import Target, PriceHelper
from Bot.Trade import Trade


class EntryStrategy(TradingStrategy):

    def __init__(self, trade: Trade, fx: FXConnector, trade_updated=None, nested=False, exchange_info=None, balance=None):
        super().__init__(trade, fx, trade_updated, nested, exchange_info, balance)
        self.smart_order = None
        self.current_target = None
        self.last_smart_price = 0

    def ensure_smart_order(self):
        smart_target = self.current_smart_target()

        # no smart targets available
        if not smart_target:
            return

        if self.current_target != smart_target:
            self.current_target = smart_target

            self.smart_order = SmartOrder(is_buy=self.trade_side().is_buy(),
                                      price=smart_target.price,
                                      sl_threshold=self.get_trade_section().sl_threshold,
                                      logger=self.logger,
                                      best_price=self.get_trade_section().best_price)


    def update_trade(self, trade: Trade):
        self.trade = trade
        self.current_target = None
        # self.init_smart_order()

    def place_market_orders(self):
        return False

    def execute(self, new_price):
        try:
            if self.is_completed():
                return

            if self.validate_all_completed():
                self.logInfo('All Orders are Completed')
                return

            self.ensure_smart_order()

            if not self.current_target:
                return

            price = self.get_single_price(new_price, self.price_selector(self.trade_side()))

            if not self.smart_order.is_init():
                ph = PriceHelper.create_price_helper(self.current_target.price)
                actual_price = ph.get_value(price)
                self.smart_order.init_price(actual_price)

                # we can use here not just a price, but cp+5%
                self.current_target.price = actual_price
                self.trigger_target_updated()

            # TODO: add automatic order placement if it was canceled by someone
            trigger_order_price = self.smart_order.price_update(price)
            self.handle_smart_target(trigger_order_price, price)
        except BinanceAPIException as bae:
            self.logError(str(bae))

    def get_trade_volume(self, exchange_rate):
        #if buying asset using % value of the volume
        if self.trade_side().is_buy() and self.current_target.vol.is_rel():
            buying_currency_vol = self.current_target.vol.get_val(self.secondary_asset_balance().avail)
            # self.exchange_info.adjust_quanity(t.vol)
            return buying_currency_vol / exchange_rate

        return self.current_target.vol.get_val(self.trade.get_cap(self.balance.avail))

    def handle_smart_target(self, trigger_order_price, current_price):
        if not trigger_order_price:
            return
        if self.place_market_orders():
            self.handle_market_order(trigger_order_price, current_price)
        else:
            self.handle_stoploss_order(trigger_order_price, current_price)

    def handle_market_order(self, trigger_order_price, current_price):
        if (self.trade_side().is_sell() and trigger_order_price > current_price) or \
                (self.trade_side().is_buy() and trigger_order_price < current_price):
            self.logInfo(
                'Trigger Order Price {:.08f}; Current Price {:.08f}'.format(trigger_order_price, current_price))

            # t = self.current_smart_target()

            # vol = t.vol.get_val(self.balance.avail)
            vol = self.get_trade_volume(current_price)

            order = self.fx.create_makret_order(
                self.symbol(),
                self.trade_side().name,
                self.exchange_info.adjust_quanity(
                    self.exchange_info.adjust_quanity(vol))
            )

            self.current_target.set_active(order['orderId'])
            self.current_target.set_completed()
            self.trigger_target_updated()
            return

        if self.update_last_smart_price(trigger_order_price):
            self.trigger_target_updated()

    def handle_stoploss_order(self, trigger_order_price, current_price):
        if self.need_update_last_trigger_price(trigger_order_price):
            self.logInfo('Setting StopLoss-{} for {:.08f} - {} of current Price: {:.08f}'.format(self.trade_side().name,
                                                                                                 trigger_order_price,
                                                                                                 self.get_trade_section().sl_threshold,
                                                                                                 current_price))

            if self.current_target.is_active():
                try:
                    status = self.fx.get_order_status(self.symbol(), self.current_target.id)

                    if self.fx.cancel_order(self.symbol(), self.current_target.id):
                        self.current_target.set_canceled()
                        self.trigger_target_updated()
                        self.balance.avail = float(status["origQty"]) - float(status["executedQty"])
                except BinanceAPIException:
                    self.logError(traceback.format_exc())


            th_sl_price = self.smart_order.sl_threshold.get_val(self.current_target.price)

            if self.trade_side().is_buy():
                limit = max(trigger_order_price + th_sl_price, self.current_target.price + th_sl_price)
            else:
                limit = min(trigger_order_price - th_sl_price, self.current_target.price - th_sl_price)

                # vol = t.vol.get_val(self.balance.avail)
            vol = self.get_trade_volume(current_price)

            try:
                order = self.fx.create_stop_order(
                    sym=self.symbol(),
                    side=self.trade_side().name,
                    stop_price=self.exchange_info.adjust_price(trigger_order_price),
                    price=self.exchange_info.adjust_price(limit),
                    volume=self.exchange_info.adjust_quanity(vol)
                )
            except BinanceAPIException as sl_exception:
                if sl_exception.message.lower().find('order would trigger immediately') > -1:
                    order = self.fx.create_makret_order(
                        self.symbol(),
                        self.trade_side().name,
                        self.exchange_info.adjust_quanity(
                            self.exchange_info.adjust_quanity(vol))
                    )
                else:
                    raise

            self.update_last_smart_price(trigger_order_price)
            self.current_target.set_active(order['orderId'])
            self.trigger_target_updated()

    def update_last_smart_price(self, trigger_price):
        if self.need_update_last_trigger_price(trigger_price):
            self.get_trade_section().best_price = trigger_price
            self.last_smart_price = trigger_price
            return True
        return False

    def need_update_last_trigger_price(self, trigger_price):
        return (self.trade_side().is_sell() and trigger_price > self.last_smart_price) or \
               (self.trade_side().is_buy() and trigger_price < self.last_smart_price) or \
               self.last_smart_price == 0

    def trade_side(self):
        return self.get_trade_section().side if self.get_trade_section().side else self.trade.side.reverse()

    def is_completed(self):
        return self.get_trade_section().is_completed()

    def current_smart_target(self):
        targets = self.get_trade_section().get_all_incomplete_smart_targets()
        if len(targets) > 0:
            return targets[0]
        else:
            return None

    def validate_all_orders(self, targets):
        return all(t.is_completed() or (t.status.is_active() or t.has_id()) for t in targets)

    def validate_all_completed(self):
        return len(self.get_trade_section().get_all_incomplete_smart_targets()) == 0

    def get_trade_section(self):
        return self.trade.entry

    def on_order_status_changed(self, t: Target, data):
        if not t.is_entry_target():
            return

        if t.is_completed():
            self.logInfo('Target {} completed'.format(t))
        else:
            self.logInfo('Order status updated: {}'.format(t.status))


class ExitStrategy(EntryStrategy):
    def __init__(self, trade: Trade, fx: FXConnector, trade_updated=None, nested=False, exchange_info=None, balance=None):
        super().__init__(trade, fx, trade_updated, nested, exchange_info, balance)

    def get_trade_section(self):
        return self.trade.exit

    def trade_side(self):
        return self.get_trade_section().side if self.get_trade_section().side else self.trade.side

    def on_order_status_changed(self, t: Target, data):
        if not t.is_exit_target():
            return

        if t.is_completed():
            self.logInfo('Target {} completed'.format(t))
        else:
            self.logInfo('Order status updated: {}'.format(t.status))



