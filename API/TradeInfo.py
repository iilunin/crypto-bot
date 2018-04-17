from Bot.AccountBalances import Balance, AccountBalances
from Bot.Strategy.TargetsAndStopLossStrategy import TargetsAndStopLossStrategy
from Bot.Strategy.TradingStrategy import TradingStrategy


class TradeInfo:
    def __init__(self, strategy: TradingStrategy):
        self.status = None
        self.symbol = None
        self.balance = 0

        self.possible_strategies = []
        self.active_strategy = None
        self.active_target = None

        self.stop_loss_traget = None
        self.entry_target = None
        self.exit_targets = []


        if strategy:
            self.extract_info(strategy)

    def extract_info(self, strategy):
        trade = strategy.trade
        self.symbol = trade.symbol
        self.status = trade
        self.balance = AccountBalances().get_balance(trade.asset)

        if isinstance(strategy, TargetsAndStopLossStrategy):
            if strategy.strategy_sl:
                sl_name = self.class_name(strategy.strategy_sl)
                if strategy.strategy_sl.is_stoploss_order_active():
                    self.active_strategy = sl_name

                self.possible_strategies.append(sl_name)

            if strategy.strategy_entry and not strategy.strategy_entry.is_completed() and trade.is_new():
                enty_name = self.class_name(strategy.strategy_exit)
                self.active_strategy = enty_name
                self.possible_strategies.append(enty_name)


    def class_name(self, obj):
        return obj.__class__.__name__