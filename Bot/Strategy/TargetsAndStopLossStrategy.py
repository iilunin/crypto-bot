from binance.exceptions import BinanceAPIException

from Bot.AccountBalances import AccountBalances
from Bot.FXConnector import FXConnector
from Bot.TradeEnums import OrderStatus
from Bot.Strategy.EntryStrategy import EntryStrategy, ExitStrategy
from Bot.Strategy.PlaceOrderStrategy import PlaceOrderStrategy
from Bot.Strategy.StopLossStrategy import StopLossStrategy
from Bot.Strategy.TradingStrategy import TradingStrategy
from Bot.Target import Target
from Bot.Trade import Trade


class TargetsAndStopLossStrategy(TradingStrategy):
    def __init__(self, trade: Trade, fx: FXConnector, trade_updated=None, balance=None):
        super().__init__(trade=trade, fx=fx, trade_updated=trade_updated, balance=balance)

        if trade.has_stoploss():
            self.create_sl_strategy(trade)
        else:
            self.strategy_sl = None

        self.strategy_entry = EntryStrategy(trade, fx, trade_updated, True, self.exchange_info, self.balance) \
            if trade.has_entry() and not trade.entry.is_completed() else None

        if trade.has_exit() and not trade.exit.is_completed():
            self.create_exit_strategy(trade)
        else:
            self.strategy_exit = None

        self.last_price = {}


    def create_sl_strategy(self, trade):
        self.strategy_sl = StopLossStrategy(trade, self.fx, self.trade_updated, True, self.exchange_info, self.balance)

    def create_exit_strategy(self, trade):
        self.strategy_exit = PlaceOrderStrategy(trade, self.fx, self.trade_updated, True, self.exchange_info,
                                                self.balance)
        # if trade.exit.type.is_smart():
        #     self.strategy_exit = ExitStrategy(trade, self.fx, self.trade_updated, True, self.exchange_info,
        #                                       self.balance)
        # elif trade.exit.type.is_target():


    def update_trade(self, trade: Trade):
        super().update_trade(trade)
        self.last_execution_price = 0

        # [s.update_trade(trade) for s in self.all_strategies()]
        if trade.has_stoploss():
            if self.strategy_sl:
                self.strategy_sl.update_trade(trade)
            else:
                self.strategy_sl = self.create_sl_strategy(trade)
        else:
            self.strategy_sl = None

        # new trade has exit
        if trade.has_exit():
            if self.strategy_exit:
                self.strategy_exit.update_trade(trade)
            else:
                self.create_exit_strategy(trade)
        else:
            self.strategy_exit = None

        if self.strategy_entry and trade.is_new():
            self.strategy_entry.update_trade(trade)

    def execute(self, new_price):
        if self.is_completed():
            self.logInfo('Trade Complete')
            return

        self.last_price = new_price

        if (self.strategy_sl and self.strategy_sl.is_completed()) \
                or (self.strategy_exit and self.strategy_exit.is_completed()):
            self.set_trade_completed()
            return

        # self.log_price(new_price)

        if new_price == self.last_execution_price:
            return

        self.last_execution_price = new_price

        if self.trade.status.is_new():
            if self.strategy_entry:
                self.strategy_entry.execute(new_price)
                # # implementy market entry
                # self.trade.status = OrderStatus.ACTIVE
                # self.trade_updated(self.trade)
            else: # if no entry is needed
                self.trade.set_active()
                self.trigger_target_updated()

        if self.trade.status.is_active():
            sl_active = False
            if self.strategy_sl:
                self.strategy_sl.execute(new_price)
                sl_active = self.strategy_sl.is_stoploss_order_active()

            if self.strategy_exit and not sl_active:
                self.strategy_exit.execute(new_price)

    def on_order_status_changed(self, t: Target, data):
        complete_trade = False

        if t.is_completed():
            if t.is_entry_target():
                # validate balance and activate trade only if there are trading targets
                if self.strategy_exit:
                    AccountBalances().update_balances(self.fx.get_all_balances_dict())
                    self.trade.cap = self.get_balance_for_side().avail
                    self.trade.set_active()
                    self.trigger_target_updated()
                else:
                    complete_trade = True
            elif t.is_exit_target():
                if self.trade.exit and self.trade.exit.is_completed():
                    # if all targets are completed, set trade as completed
                    complete_trade = True
            elif t.is_stoploss_target():
                complete_trade = True

        if complete_trade:
            self.set_trade_completed()

        [s.on_order_status_changed(t, data) for s in self.all_strategies()]
        # if self.strategy_sl:
        #     self.strategy_sl.order_status_changed(t, data)
        #
        # if self.strategy_exit:
        #     self.strategy_exit.order_status_changed(t, data)
        #
        # if self.strategy_entry:
        #     self.strategy_entry.order_status_changed(t, data)

    def all_strategies(self):
        s = []
        if self.strategy_sl:
            s.append(self.strategy_sl)

        if self.strategy_exit:
            s.append(self.strategy_exit)

        if self.strategy_entry:
            s.append(self.strategy_entry)

        return s

    def emergent_close_position(self):
        try:
            self.paused = True
            self.fx.cancel_open_orders(self.symbol())

            AccountBalances().update_balances(self.fx.get_all_balances_dict())

            # price = self.exchange_info.adjust_price(self.get_sl_limit_price())
            bal = self.trade.get_cap(self.get_balance_for_side().avail)

            volume = round(bal / self.get_single_price(self.last_price), 8) if self.trade_side().is_buy() else bal
            adjusted_vol = self.exchange_info.adjust_quanity(volume)

            self.logInfo(
                'Closing positions ({}): {}, v: {:.08f}'.format(self.symbol(), self.trade_side(), adjusted_vol))

            if adjusted_vol > 0:
                order = self.fx.create_makret_order(self.symbol(),
                                                    self.trade_side().name,
                                                    adjusted_vol)

            self.logInfo('Positions [{}] Closed'.format(self.symbol()))
            self.trade.set_completed()
            self.trigger_target_updated()
        except BinanceAPIException as bae:
            self.logError(str(bae))

