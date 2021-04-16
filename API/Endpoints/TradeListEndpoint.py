from API.Endpoints.BotAPIResource import BotAPIResource
from flask_jwt_extended import jwt_required

class TradeListEndpoint(BotAPIResource):
    @jwt_required()
    def get(self):
        return [{
            'id': s.trade.id,
            'sym': s.symbol(),
            'avail': s.balance.avail,
            'locked': s.balance.locked,
            'paused': s.paused,
            'price': s.get_single_price(s.last_price),
            'sell': s.trade.is_sell()} for s in self.th.strategies]