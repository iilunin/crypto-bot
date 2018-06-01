from flask import Flask, Response
from flask_restful import reqparse, abort, Api, Resource
from flask_cors import CORS
import json

from API.APIResult import APIResult
from Bot.ConfigLoader import ConfigLoader
from Bot.TradeHandler import TradeHandler
from Utils.Logger import Logger


class APIServer:
    VERSION = 'v1'
    API_PREFIX = '/api/'+VERSION

    def __init__(self, trade_handler: TradeHandler):
        self.th = trade_handler
        self.app = Flask(__name__)
        self.api = Api(self.app)
        CORS(self.app)

        self.app.config['SECRET_KEY'] = 'VERY_SECRET_KEY_GOES_HERE'

        self.api.add_resource(TradeList, APIServer.API_PREFIX + '/trades',
                              resource_class_kwargs={'trade_handler': self.th})
        self.api.add_resource(Trade, APIServer.API_PREFIX + '/trade/<id>',
                              resource_class_kwargs={'trade_handler': self.th})
        self.api.add_resource(Managment, APIServer.API_PREFIX + '/management/<action>',
                              resource_class_kwargs={'trade_handler': self.th})


    def run(self, port):
        self.app.run(debug=True, port=port, use_reloader=False)


class BotAPIREsource(Resource, Logger):
    def __init__(self, trade_handler: TradeHandler):
        Resource.__init__(self)
        Logger.__init__(self)
        self.th: TradeHandler = trade_handler


class TradeList(BotAPIREsource):
    def get(self):
        return [{
            'id': s.trade.id,
            'sym': s.symbol(),
            'avail': s.balance.avail,
            'locked': s.balance.locked,
            'paused': s.paused,
            'price': s.get_single_price(s.last_price),
            'sell': s.trade.is_sell()} for s in self.th.strategies]


class Trade(BotAPIREsource):
    def __init__(self, trade_handler):
        super().__init__(trade_handler)
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('action', type=str, help='close|start|pause')

    def get(self, id):
        return Response(response=ConfigLoader.get_json_str(self.th.get_strategy_by_id(id).trade),
                        status=200,
                        mimetype="application/json")

    def delete(self, id):
        strategies = self.get_strategies(id)

        if not strategies:
            return APIResult.ErrorResult(101, msg='No strategies were found')

        # for strategy in strategies:
        #     self.th.remove_trade_by_strategy(strategy, True)

        return APIResult.OKResult()

    def get_strategies(self, id):
        if id == '0':
            strategies = self.th.strategies
        else:
            strategy = self.th.get_strategy_by_id(id)
            strategies = None if not strategy else [strategy]
        return strategies

    def put(self, trade_json):
        pass

    def post(self, id=None):
        args = self.parser.parse_args()
        action = args['action']

        if not action:
            return APIResult.ErrorResult(100, msg='No "action" was provided')

        strategies = self.get_strategies(id)

        if not strategies:
            return APIResult.ErrorResult(101, msg='No strategies were found')

        action = action.lower()

        if action == 'close':
            for strategy in strategies:
                strategy.emergent_close_position()

        elif action in ['pause', 'resume']:
            paused = True if action == 'pause' else False

            for strategy in strategies:
                strategy.paused = paused

        return APIResult.OKResult()

class Managment(BotAPIREsource):
    def post(self, action):
        if not action:
            return 'action should be \'pause\' or \'start\''

        action = action.lower()

        if action == 'pause':
            self.th.pause()

        elif action == 'start':
            self.th.resume()

        elif action == 'cancel':
            pass

        return {}
