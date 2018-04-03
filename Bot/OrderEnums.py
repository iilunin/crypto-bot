from enum import Enum

class OrderStatus(Enum):
    NEW = 'new'
    COMPLETED = 'completed'
    ACTIVE = 'active'

class Side(Enum):
    BUY = 'buy'
    SELL = 'sell'
