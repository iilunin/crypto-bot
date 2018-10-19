import os
from calendar import timegm
from datetime import datetime

import flask
from flask import request
from flask_jwt_simple import create_jwt, jwt_required, get_jwt_identity

from API.Entities.APIResult import APIResult
from API.Endpoints.BotAPIResource import BotAPIResource


class JWTEndpoint(BotAPIResource):
    user: str = os.getenv('API_USER', 'bot')
    pwd: str = os.getenv('API_PASS', 'botpwd')

    def __init__(self, trade_handler):
        super().__init__(trade_handler)

    # Provide a method to create access tokens. The create_jwt()
    # function is used to actually generate the token
    def post(self):
        if not request.is_json:
            return APIResult.ErrorResult(100, msg="Missing JSON in request"), 400

        params = request.get_json()
        username = params.get('username', None)
        password = params.get('password', None)

        if not username:
            return APIResult.ErrorResult(status=101, msg="Missing username parameter"), 400
        if not password:
            return APIResult.ErrorResult(status=101, msg="Missing password parameter"), 400

        if username != JWTEndpoint.user or password != JWTEndpoint.pwd:
            return APIResult.ErrorResult(status=101, msg="Bad username or password"), 401

        # Identity can be any data that is json serializable


        ret = {'jwt': create_jwt(identity=username),
               'exp': timegm((flask.current_app.config['JWT_EXPIRES'] + datetime.now()).utctimetuple())}
        return ret, 200

    # Protect a view with jwt_required, which requires a valid jwt
    # to be present in the headers.
    @jwt_required
    def get(self):
        # Access the identity of the current user with get_jwt_identity
        return {'hello_from': get_jwt_identity()}, 200