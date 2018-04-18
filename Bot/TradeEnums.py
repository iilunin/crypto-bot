from enum import Enum

class OrderStatus(Enum):
    NEW = 'new'
    COMPLETED = 'completed'
    ACTIVE = 'active'

    def is_new(self):
        return self == OrderStatus.NEW

    def is_completed(self):
        return self == OrderStatus.COMPLETED

    def is_active(self):
        return self == OrderStatus.ACTIVE

class Side(Enum):
    BUY = 'buy'
    SELL = 'sell'

    def is_buy(self):
        return self == Side.BUY

    def is_sell(self):
        return self == Side.SELL

    def reverse(self):
        if self == Side.BUY:
            return Side.SELL
        return Side.BUY
#
# class Entry(Enum):
#     SMART = 'smart'
#     TARGET = 'target'
#
#     def is_smart(self):
#         return self == Entry.SMART
#
#     def is_target(self):
#         return self == Entry.TARGET
