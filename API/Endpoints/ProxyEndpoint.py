import io
import requests

from flask import send_file

from API.Endpoints.BotAPIResource import BotAPIResource


class ProxyEndpoint(BotAPIResource):

    def get(self):
        r = requests.get('https://img.shields.io/github/stars/iilunin/crypto-bot.svg?style=social&label=Star&maxAge=2592000')
        return send_file(io.BytesIO(r.content), mimetype='image/svg+xml;charset=utf-8', as_attachment=False)
