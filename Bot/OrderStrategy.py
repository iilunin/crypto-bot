from Bot import StopLossSettings
from Bot.FXConnector import FXConnector
from Bot.Order import Order
from Bot.OrderStatus import OrderStatus
from Bot.StopLossSettings import StopLossSettings
from Bot.Value import Value


class OrderStrategy:
    def __init__(self, order: Order, fx: FXConnector):
        self.order = order
        self.fx = fx
        self.available = 0.
        self.locked = 0.
        self.exchange_info = self.fx.get_exchange_info(self.symbol())

    def symbol(self):
        return self.order.symbol

    def execute(self, new_price):
        pass

    def validate_asset_size(self):
        self.available, self.locked = self.fx.get_balance(self.order.asset)


class TargetsAndStopLossStrategy(OrderStrategy):

    def __init__(self, order: Order, fx: FXConnector):
        super().__init__(order, fx)
        self.current_stop_loss = 0
        self.adjust_stoploss_price()
        self.simulate = False

    def execute(self, new_price):
        self.adjust_stoploss_price(new_price)
        self.adjust_stoploss_order(new_price)

        print('SL:{:.08f}'.format(self.current_stop_loss))

    def adjust_stoploss_price(self, current_price=None):
        stop_customization = [o for o in self.order.get_closed_targets()]

        if len(stop_customization) > 0 and stop_customization[-1].has_custom_stop():
            # sort by order value
            self.current_stop_loss = stop_customization[-1].sl
            return

        if current_price is None:
            self.current_stop_loss = self.order.get_initial_stop().price
            return

        expected_stop_loss = 0
        if self.order.sl_settings.type == StopLossSettings.Type.TRAILING:

            trialing_val = self.order.sl_settings.val

            if trialing_val.type == Value.Type.ABS:
                expected_stop_loss = current_price + (-1 if self.order.is_sell_order() else 1) * trialing_val.v
            else:
                expected_stop_loss = current_price * (1 + (-1 if self.order.is_sell_order() else 1) * trialing_val.v/100)

            expected_stop_loss = round(expected_stop_loss, 8)
            if self.order.is_sell_order() and expected_stop_loss > self.current_stop_loss:
                self.current_stop_loss = expected_stop_loss
            elif not self.order.is_sell_order() and expected_stop_loss < self.current_stop_loss:
                self.current_stop_loss = expected_stop_loss

        print('SL:{:.08f}, EXP:{:.08f}, P:{:.08f}'.format(self.current_stop_loss, expected_stop_loss, current_price))

    def adjust_stoploss_order(self, current_price):
        threshold = round(self.current_stop_loss * self.order.sl_settings.threshold, 8)

        if (self.order.is_sell_order() and (self.current_stop_loss + threshold) >= current_price) or \
            (not self.order.is_sell_order() and (self.current_stop_loss - threshold) <= current_price):
            self.set_stoploss_order()
        else:
            self.cancel_stoploss_orders()

    def set_stoploss_order(self):
        # if we have order in place
        if self.order.sl_settings.initial_target.id:
            print('validating stoploss order')
            if False: # validate it
                return
            else:
                pass

        if self.simulate:
            order = self.fx.create_test_stop_order(self.symbol(), self.order.side.name, self.current_stop_loss, 50)
            order['orderId'] = 2333123
        else:
            self.cancel_all_orders()

            order = self.fx.create_stop_order(
                self.symbol(),
                self.order.side.name,
                self.exchange_info.adjust_price(self.current_stop_loss),
                self.exchange_info.adjust_quanity(self.available)
            )

        self.order.sl_settings.initial_target.id = order['orderId']
        print('setting stop loss order')
        pass

    def cancel_all_orders(self):
        print('canceling all orders')
        pass

    def cancel_stoploss_orders(self):
        if not self.order.sl_settings.initial_target.id:
            return

        print('canceling stoploss orders')
        pass