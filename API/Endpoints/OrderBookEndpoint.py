from API.Endpoints.BotAPIResource import BotAPIResource
from flask_jwt_extended import jwt_required


class OrderBookEndpoint(BotAPIResource):

    @jwt_required()
    def get(self, symbol):
        return self.th.fx.get_orderbook_tickers(symbol)
