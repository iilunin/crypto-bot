import json

from flask import Response
from flask_jwt_extended import jwt_required
from flask_restful import reqparse

from API.Endpoints.BotAPIResource import BotAPIResource
from API.Entities.APIResult import APIResult
from Bot.ConfigLoader import ConfigLoader


class TradeEndpoint(BotAPIResource):
    def __init__(self, trade_handler):
        super().__init__(trade_handler)
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('action', type=str, help='close|start|pause')
        self.parser.add_argument('data', type=dict)

    @jwt_required()
    def get(self, id):
        return Response(response=ConfigLoader.get_json_str(self.th.get_strategy_by_id(id).trade),
                        status=200,
                        mimetype="application/json")

    @jwt_required()
    def delete(self, id):
        strategies = self.get_strategies(id)

        if not strategies:
            return APIResult.ErrorResult(101, msg='No strategies were found'), 404

        for strategy in strategies:
            self.th.remove_trade_by_strategy(strategy, True)

        return APIResult.OKResult()

    @jwt_required()
    def get_strategies(self, id):
        if id == '0':
            strategies = self.th.strategies
        else:
            strategy = self.th.get_strategy_by_id(id)
            strategies = None if not strategy else [strategy]
        return strategies

    @jwt_required()
    def put(self, trade_json):
        pass

    @jwt_required()
    def post(self, id=None):
        args = self.parser.parse_args()
        action = args['action']

        if not action:
            return APIResult.ErrorResult(100, msg='No "action" was provided'), 403

        strategies = self.get_strategies(id)

        if not strategies and id != '0':
            return APIResult.ErrorResult(101, msg='No strategies were found'), 404

        action = action.lower()

        if action == 'close':
            for strategy in strategies:
                strategy.emergent_close_position()

        elif action in ['pause', 'resume']:
            paused = True if action == 'pause' else False

            for strategy in strategies:
                strategy.paused = paused
        elif action == 'add':
            ids = []
            try:
                trade_json = args['data']
                trades = ConfigLoader.load_trade_list_from_obj(trade_json)
                for trade in trades:
                    ids.append(trade.id)
                    self.th.updated_trade(trade)
                    self.th.fire_trade_updated(trade, True)
            except Exception as e:
                return json.dumps(APIResult.ErrorResult(100, str(e))), 500

            return APIResult.OKResult(ids), 201

        return APIResult.OKResult(), 200