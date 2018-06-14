from flask import Flask, Response, app, render_template
from flask_restful import reqparse, abort, Api, Resource
from flask_cors import CORS
import json

from API.APIResult import APIResult
from Bot.ExchangeInfo import ExchangeInfo
from Bot.ConfigLoader import ConfigLoader
from Bot.TradeHandler import TradeHandler
from Utils.Logger import Logger


app = Flask(__name__, static_folder='templates', static_url_path='')

@app.route('/')
@app.route('/trades')
def index():
    return render_template('index.html')


class APIServer:
    VERSION = 'v1'
    API_PREFIX = '/api/'+VERSION

    def __init__(self, trade_handler: TradeHandler):
        self.th = trade_handler
        self.app = app
        self.api = Api(self.app)
        CORS(self.app)

        self.app.config['SECRET_KEY'] = 'VERY_SECRET_KEY_GOES_HERE'

        self.api.add_resource(TradeList, APIServer.API_PREFIX + '/trades',
                              resource_class_kwargs={'trade_handler': self.th})
        self.api.add_resource(Trade, APIServer.API_PREFIX + '/trade/<id>',
                              resource_class_kwargs={'trade_handler': self.th})
        # self.api.add_resource(Managment, APIServer.API_PREFIX + '/management/<action>',
        #                       resource_class_kwargs={'trade_handler': self.th})

        self.api.add_resource(APIExchangeInfo, APIServer.API_PREFIX + '/info',
                              resource_class_kwargs={'trade_handler': self.th})

    def run(self, port):
        self.app.run(host='0.0.0.0', debug=True, port=port, use_reloader=False)


class BotAPIREsource(Resource, Logger):
    def __init__(self, trade_handler: TradeHandler):
        Resource.__init__(self)
        Logger.__init__(self)
        self.th: TradeHandler = trade_handler


class APIExchangeInfo(BotAPIREsource):
    def get(self):
        return list(ExchangeInfo().get_all_symbols())

    def post(self):
        args = self.parser.parse_args()
        action = args['action']

        if not action:
            return APIResult.ErrorResult(100, msg='No "action" was provided'), 403

        if action == 'reconnect':
            self.th.force_reconnect_sockets()


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
        self.parser.add_argument('data', type=dict)

    def get(self, id):
        return Response(response=ConfigLoader.get_json_str(self.th.get_strategy_by_id(id).trade),
                        status=200,
                        mimetype="application/json")

    def delete(self, id):
        strategies = self.get_strategies(id)

        if not strategies:
            return APIResult.ErrorResult(101, msg='No strategies were found'), 404

        for strategy in strategies:
            self.th.remove_trade_by_strategy(strategy, True)

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
            return APIResult.ErrorResult(100, msg='No "action" was provided'), 403

        strategies = self.get_strategies(id)

        if not strategies:
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

# class Managment(BotAPIREsource):
#     def post(self, action):
#         if not action:
#             return 'action should be \'pause\' or \'start\''
#
#         action = action.lower()
#
#         if action == 'pause':
#             self.th.pause()
#
#         elif action == 'start':
#             self.th.resume()
#
#         elif action == 'cancel':
#             pass
#
#         return {}
