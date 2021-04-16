from flask_jwt_extended import jwt_required

from API.Endpoints.BotAPIResource import BotAPIResource
from API.Entities.APIResult import APIResult
from Bot.ExchangeInfo import ExchangeInfo


class APIExchangeInfoEndpoint(BotAPIResource):
    @jwt_required()
    def get(self):
        return list(ExchangeInfo().get_all_symbols())

    @jwt_required()
    def post(self):
        args = self.parser.parse_args()
        action = args['action']

        if not action:
            return APIResult.ErrorResult(100, msg='No "action" was provided'), 403

        if action == 'reconnect':
            self.th.force_reconnect_sockets()