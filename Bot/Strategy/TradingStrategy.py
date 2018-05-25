from binance.exceptions import BinanceAPIException

from Bot.ExchangeInfo import ExchangeInfo
from Bot.AccountBalances import AccountBalances
from Bot.AccountBalances import Balance
from Bot.FXConnector import FXConnector
from Bot.Target import Target, PriceHelper
from Bot.Trade import Trade

from Utils.Logger import Logger


class TradingStrategy(Logger):
    def __init__(self,
                 trade: Trade,
                 fx: FXConnector,
                 trade_updated=None,
                 nested=False,
                 exchange_info=None,
                 balance: Balance=None):
        self.trade: Trade = trade
        self.fx = fx
        self.balance: Balance = balance if balance else Balance()
        self._exchange_info = None
        self.simulate = False
        self.trade_updated = trade_updated
        self.last_execution_price = 0
        self.paused = False

        super().__init__()

        if nested:
            if balance:
                self.balance = balance
        else:
            self.init()

    @property
    def exchange_info(self):
        if not self._exchange_info:
            self._exchange_info = ExchangeInfo().symbol_info(self.symbol())

        return self._exchange_info

    def _get_logger_name(self):
        return '{}({})'.format(self.__class__.__name__, self.symbol())

    def update_trade(self, trade: Trade):
        self.trade = trade
        self.init(True)

    def init(self, force_cancel_open_orders=False):
        # #TODO: make one call for each symbols
        # if not force_cancel_open_orders:
        #     self.exchange_info = self.fx.get_exchange_info(self.symbol())
        # self.exchange_info = self.ExchangeInfo().symbol_info(self.symbol())
        self.validate_target_orders(force_cancel_open_orders)

    def is_completed(self):
        return self.trade.is_completed()

    def trade_side(self):
        return self.trade.side

    def self_update_balances(self):
        AccountBalances().update_balances(self.fx.get_all_balances_dict())

    def asset(self):
        return self.trade.asset.upper()

    def secondary_asset(self):
        return self.symbol().replace(self.asset(), '')

    def secondary_asset_balance(self):
        return AccountBalances().get_balance(self.secondary_asset())

    def symbol(self):
        return self.trade.symbol

    def emergent_close_position(self):
        raise NotImplementedError('Strategy does not support this method')

    def on_execution_rpt(self, data):
        self.logInfo('Execution Rpt: {}'.format(data))
        orderId = data['orderId']

        tgts = self.trade.get_all_active_placed_targets()

        for t in tgts:
            if t.id == orderId:
                if self._update_trade_target_status_change(t, data['status']):
                    self.last_execution_price = 0
                    self.trigger_target_updated()
                    self.on_order_status_changed(t, data)
                break

    def on_order_status_changed(self, t: Target, data):
        pass

    def validate_target_orders(self, force_cancel_open_orders=False):
        NEW_STATUSES = [FXConnector.ORDER_STATUS_NEW, FXConnector.ORDER_STATUS_PARTIALLY_FILLED]

        try:
            exchange_orders = self.fx.get_all_orders(self.symbol())
            has_open_orders = any([eo['status'] in NEW_STATUSES for eo in exchange_orders.values()])

        except BinanceAPIException as bae:
            self.logError(str(bae))
            return

        active_trade_targets = self.trade.get_all_active_placed_targets()

        update_required = False
        if force_cancel_open_orders or (len(active_trade_targets) == 0 and has_open_orders):
            self.logInfo('Cancelling all Open orders')
            self.fx.cancel_open_orders(self.symbol())
        else:
            for active_trade_target in active_trade_targets:

                if active_trade_target.id not in exchange_orders:
                    active_trade_target.set_canceled()
                    update_required = True
                else:
                    s = exchange_orders[active_trade_target.id]['status']
                    if s in NEW_STATUSES:

                        # check if price in file is the same as on the exchange
                        trade_prices = {self.exchange_info.adjust_price(active_trade_target.price)}
                        if active_trade_target.is_smart():
                            trade_prices.add(self.exchange_info.adjust_price(active_trade_target.best_price))

                        exchange_prices = {float(exchange_orders[active_trade_target.id]['price']),
                                           float(exchange_orders[active_trade_target.id]['stop_price'])}

                        if not PriceHelper.is_float_price(active_trade_target.price) or len(
                                trade_prices & exchange_prices) == 0:
                            self.logInfo('Target price changed: {}'.format(active_trade_target))
                            self.fx.cancel_order(self.symbol(), active_trade_target.id)
                            active_trade_target.set_canceled()
                            update_required = True

                    update_required |= self._update_trade_target_status_change(active_trade_target, s)

            if update_required:
                self.trigger_target_updated()

    def _update_trade_target_status_change(self, t: Target, status: str) -> bool:
        if status == FXConnector.ORDER_STATUS_FILLED:
            t.set_completed()
            return True

        if status in [FXConnector.ORDER_STATUS_CANCELED,
                      FXConnector.ORDER_STATUS_REJECTED,
                      FXConnector.ORDER_STATUS_EXPIRED]:
            t.set_canceled()
            return True

        return False

    def get_balance_for_side(self, is_sell=None):
        if not is_sell:
            is_sell = self.trade_side().is_sell()

        return self.balance if is_sell else self.secondary_asset_balance()

    def execute(self, new_price):
        pass

    # def update_asset_balance(self, avail, locked):
    #     self.balance.avail = avail
    #     self.balance.locked = locked

    # def validate_asset_balance(self):
    #     self.balance.avail, self.balance.locked = self.fx.get_balance(self.trade.asset)

    def set_trade_completed(self):
        if not self.trade.is_completed():
            self.trade.set_completed()
            self.trigger_target_updated()

    def set_trade_removed(self):
        self.trade.set_removed()
        self.trigger_target_updated()

    def trigger_target_updated(self, sync_cloud=True):
        if self.trade_updated:
            self.trade_updated(self.trade, sync_cloud)

    def get_bid_ask(self, price):
        return price['b'], price['a']

    def get_single_price(self, price, selector=None):
        if not selector:
            selector = self.price_selector()

        return price[selector]

    def get_info(self):
        # return TradeInfo(self)
        pass

    def price_selector(self, side=None):
        if not side:
            side = self.trade_side()

        return 'b' if side.is_sell() else 'a'

    def __str__(self):
        return self.logger.name
