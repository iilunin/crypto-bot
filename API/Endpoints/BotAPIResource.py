from flask_restful import Resource

from Bot.TradeHandler import TradeHandler
from Utils.Logger import Logger


class BotAPIResource(Resource, Logger):
    def __init__(self, trade_handler: TradeHandler):
        Resource.__init__(self)
        Logger.__init__(self)
        self.th: TradeHandler = trade_handler