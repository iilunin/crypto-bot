from Bot.FXConnector import FXConnector
from Bot.OrderStatus import OrderStatus
from Bot.Strategy.PlaceOrderStrategy import PlaceOrderStrategy
from Bot.Strategy.StopLossStrategy import StopLossStrategy
from Bot.Strategy.TradingStrategy import TradingStrategy
from Bot.Trade import Trade


class TargetsAndStopLossStrategy(TradingStrategy):
    def __init__(self, trade: Trade, fx: FXConnector, trade_updated=None):
        super().__init__(trade, fx, trade_updated)
        self.strategy_sl = StopLossStrategy(trade, fx, trade_updated, True, self.exchange_info)
        self.strategy_po = PlaceOrderStrategy(trade, fx, trade_updated, True, self.exchange_info)

    def execute(self, new_price):
        if self.trade.status == OrderStatus.COMPLETED:
            self.logInfo('Trade Complete')
            return

        if self.trade.status == OrderStatus.NEW and self.trade.entry is not None:
            # implementy market entry
            self.trade.status = OrderStatus.ACTIVE
            self.trade_updated(self.trade)
            pass

        if self.trade.status == OrderStatus.ACTIVE:
            self.strategy_sl.execute(new_price)

            if self.strategy_sl.is_stoploss_order_active():
                self.logInfo('SL is Active')
            else:
                self.strategy_po.execute(new_price)
                pass

