from datetime import datetime

from binance.exceptions import BinanceAPIException

from Bot.ExchangeInfo import ExchangeInfo
from Bot.AccountBalances import AccountBalances
from Bot.AccountBalances import Balance
from Bot.FXConnector import FXConnector
from Bot.Target import Target, PriceHelper
from Bot.Trade import Trade
from Utils import Utils

from Utils.Logger import Logger


class TradingStrategy(Logger):
    EXCHANGE_INFO_REFRESH_S = 60

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
        self._exchange_info_last_update = datetime.now()
        self.simulate = Utils.is_simulation()
        self.trade_updated = trade_updated
        self.last_execution_price = 0
        self.paused = False
        self.last_price = {}

        super().__init__()

        if nested:
            if balance:
                self.balance = balance
        else:
            self.init()

    @property
    def exchange_info(self):
        if not self._exchange_info or \
                (datetime.now() - self._exchange_info_last_update).seconds >= TradingStrategy.EXCHANGE_INFO_REFRESH_S:
            self._exchange_info = ExchangeInfo().symbol_info(self.symbol())
            self._exchange_info_last_update = datetime.now()

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

        open_exchange_orders = {}
        recent_orders = {}
        try:
            recent_orders = self.fx.get_all_orders(self.symbol())
            open_exchange_orders = {k: v for k, v in recent_orders.items() if (v['status'] in NEW_STATUSES)}

        except BinanceAPIException as bae:
            self.logError(str(bae))
            return

        active_trade_targets = self.trade.get_all_active_placed_targets()

        update_required = False


        for active_trade_target in active_trade_targets:
            if active_trade_target.id not in open_exchange_orders:
                active_trade_target.set_canceled()
                update_required = True
            else:
                self.fx.cancel_order(self.symbol(), active_trade_target.id)

                active_trade_target.set_canceled()

                if active_trade_target.is_smart():
                    active_trade_target.best_price = 0

                update_required = True

            update_required |= self._update_trade_target_status_change(
                active_trade_target, recent_orders.get(active_trade_target.id, {}).get('status', 'UNKNOWN'))

        if force_cancel_open_orders:
            self.cancel_all_open_orders()

        if update_required:
            self.trigger_target_updated()

    def cancel_all_open_orders(self):
        self.logInfo('Cancelling all Open orders for "{}"'.format(self.symbol()))
        self.fx.cancel_open_orders(self.symbol())

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

        return price.get(selector, 0)

    def get_info(self):
        # return TradeInfo(self)
        pass

    def price_selector(self, side=None):
        if not side:
            side = self.trade_side()

        return 'b' if side.is_sell() else 'a'

    def assign_calculated_volume(self, targets):
        has_changes = False
        currency_balance = self.get_balance_for_side()

        bal = self.trade.get_cap(currency_balance.avail) + (
            currency_balance.locked if any(t.is_active() for t in targets) else 0)

        if bal <= 0:
            self.logWarning('Available balance is 0')
            return

        for t in targets:
            if t.is_completed():
                continue

            price = self.exchange_info.adjust_price(t.price)

            adjusted_balance = bal

            # in case of BUY like with BTCUSDT we have balance in USDT e.g. 700, but specifying the vol in BTC e.g. 0.1
            if self.trade_side().is_buy():
                adjusted_balance = round(bal / price, 8)

            vol = self.exchange_info.adjust_quanity(t.vol.get_val(adjusted_balance))
            if vol != t.calculated_volume:
                t.calculated_volume = vol
                has_changes = True

            if self.trade_side().is_sell():
                bal = round(bal - vol, 8)
            else:
                bal = round(bal - t.vol.get_val(bal), 8)

        return has_changes


    def __str__(self):
        return self.logger.name


    def describe(self):
        return None
