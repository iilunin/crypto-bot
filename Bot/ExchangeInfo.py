from decimal import Decimal, ROUND_DOWN, ROUND_UP

class SymbolInfo:
    def __init__(self, minPrice, maxPrice, tickSize, minQty, maxQty, stepSize, minNotional, **kvargs):
        self.minNotional = Decimal(self.strip_zeros(minNotional))
        self.stepSize = Decimal(self.strip_zeros(stepSize))
        self.maxQty = Decimal(self.strip_zeros(maxQty))
        self.minQty = Decimal(self.strip_zeros(minQty))
        self.tickSize = Decimal(self.strip_zeros(tickSize))
        self.maxPrice = Decimal(self.strip_zeros(maxPrice))
        self.minPrice = Decimal(self.strip_zeros(minPrice))

    def strip_zeros(self, s):
        return s.rstrip('0')

    def adjust_quanity(self, q, round_down=True):
        res = float(Decimal(q).quantize(self.stepSize, rounding=ROUND_DOWN if round_down else ROUND_UP))
        return float(min(max(res, self.minQty), self.maxQty))

    def adjust_price(self, q, round_down=True):
        res = round(Decimal(q), 8).quantize(self.tickSize, rounding=ROUND_DOWN if round_down else ROUND_UP)
        return float(min(max(res, self.minPrice), self.maxPrice))

class ExchangeInfo:
    __shared_state = {}

    def __init__(self):
        self.__dict__ = self.__shared_state
        if not self.__dict__:
            self.exchnage_info = {}
            self.symbols = set()

    def update(self, info):
        self.exchnage_info.update(info)
        self.symbols = set([s['symbol'] for s in self.exchnage_info['symbols']])

    def symbol_info(self, symbol):
        symbol_info = None

        for s in self.exchnage_info['symbols']:
            if s['symbol'] == symbol:
                symbol_info = s
                break

        props = {}
        for f in symbol_info['filters']:
            props.update(f)

        props.pop('filterType', None)

        return SymbolInfo(**props)

    def has_symbol(self, symbol):
        return symbol in self.symbols

    def has_all_symbol(self, symbols):
        return set(self.symbols) <= self.symbols
