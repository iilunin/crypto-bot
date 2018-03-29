from enum import Enum

class OrderStatus(Enum):
    NEW = 'new'
    ENTERED = 'entered'
    COMPLETED = 'completed'
    ACTIVE = 'active'
