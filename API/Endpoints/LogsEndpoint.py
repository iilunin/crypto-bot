from API.Endpoints.BotAPIResource import BotAPIResource
from flask_jwt_extended import jwt_required


class LogsEndpoint(BotAPIResource):

    @jwt_required()
    def get(self, file):
        if not file:
            return self.list_files()

        return self.get_file_contents(None if file == 'latest' else file)
