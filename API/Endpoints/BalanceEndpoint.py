from API.Endpoints.BotAPIResource import BotAPIResource
from flask_jwt_extended import jwt_required


class BalanceEndpoint(BotAPIResource):

    @jwt_required()
    def get(self, force='0'):
        if force == '1':
            self.th.balances.update_balances(self.th.fx.get_all_balances_dict())

        return self.th.balances.bal_dict
