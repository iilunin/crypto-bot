from datetime import datetime, timedelta
from distutils.log import Log

from flask import Flask, app, render_template
from flask_jwt_extended import JWTManager
from flask_restful import Api
from flask_cors import CORS

from API.Endpoints.LogsEndpoint import LogsEndpoint
from API.Endpoints.APIexchangeInfoEndpoint import APIExchangeInfoEndpoint
from API.Endpoints.BalanceEndpoint import BalanceEndpoint
from API.Endpoints.JWTEndpoint import JWTEndpoint
from API.Endpoints.OrderBookEndpoint import OrderBookEndpoint
from API.Endpoints.ProxyEndpoint import ProxyEndpoint
from API.Endpoints.TradeEndpoint import TradeEndpoint
from API.Endpoints.TradeListEndpoint import TradeListEndpoint
from Bot.TradeHandler import TradeHandler

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

        self.app.config['JWT_SECRET_KEY'] = 'mHZ!?9@DzdLrn@H!gy2FD46W--M*Fap!'  # TODO: Change this!
        self.app.config['SECRET_KEY'] = 'VS?cWpbD^CGa-M@h6+@pV#qCQRU3c4dn'  #  TODO: Change this!
        self.app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(weeks=48)

        self.jwt = JWTManager(app)

        self.api = Api(self.app)

        CORS(self.app)
        # self.api.add_resource(BalanceEndpoint, APIServer.API_PREFIX + '/balance',
        #                       resource_class_kwargs={'trade_handler': self.th})

        self.api.add_resource(ProxyEndpoint, APIServer.API_PREFIX + '/proxy/icon',
                              resource_class_kwargs={'trade_handler': self.th})

        self.api.add_resource(LogsEndpoint, APIServer.API_PREFIX + '/logs/<file>',
                              resource_class_kwargs={'trade_handler': self.th})

        self.api.add_resource(OrderBookEndpoint, APIServer.API_PREFIX + '/orderbook/<symbol>',
                              resource_class_kwargs={'trade_handler': self.th})

        self.api.add_resource(BalanceEndpoint, APIServer.API_PREFIX + '/balance/<force>',
                              resource_class_kwargs={'trade_handler': self.th})

        self.api.add_resource(TradeListEndpoint, APIServer.API_PREFIX + '/trades',
                              resource_class_kwargs={'trade_handler': self.th})

        self.api.add_resource(TradeEndpoint, APIServer.API_PREFIX + '/trade/<id>',
                              resource_class_kwargs={'trade_handler': self.th})

        self.api.add_resource(APIExchangeInfoEndpoint, APIServer.API_PREFIX + '/info',
                              resource_class_kwargs={'trade_handler': self.th})

        self.api.add_resource(JWTEndpoint, APIServer.API_PREFIX + '/auth',
                              resource_class_kwargs={'trade_handler': self.th})

    def run(self, port):
        self.app.run(host='0.0.0.0', debug=True, port=port, use_reloader=False)


