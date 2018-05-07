from flask import Flask, Response
from flask_restful import reqparse, abort, Api, Resource
from flask_cors import CORS
import json

from Bot.TradeHandler import TradeHandler


class APIServer:
    def __init__(self, trade_handler: TradeHandler):
        self.th = trade_handler
        self.app = Flask(__name__)
        self.api = Api(self.app)
        CORS(self.app)

        self.app.config['SECRET_KEY'] = 'VERY_SECRET_KEY_GOES_HERE'

        self.api.add_resource(TradeList, '/trades', resource_class_kwargs={'trade_handler': self.th})
        self.api.add_resource(Trade, '/reports/<id>', resource_class_kwargs={'trade_handler': self.th})

    def run(self, port):
        self.app.run(debug=True, port=port)


class BotAPIREsource(Resource):
    def __init__(self, trade_handler: TradeHandler):
        super().__init__()
        self.th: TradeHandler = trade_handler


class TradeList(BotAPIREsource):
    def get(self):
        return [{
            'id': s.trade.id,
            'sym': s.symbol(),
            'avail': s.balance.avail,
            'locked': s.balance.locked} for s in self.th.strategies]


class Trade(BotAPIREsource):
    def get(self):
        return self.th.strategies
