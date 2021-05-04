import datetime
from flask import Request, request

from API.Endpoints.BotAPIResource import BotAPIResource
from flask_jwt_extended import jwt_required
import arrow


class LogsEndpoint(BotAPIResource):

    @jwt_required()
    def get(self, file=None, limit=1000):

        file = request.args.get('file', file)
        limit = int(request.args.get('limit', 1000))

        if not file:
            return self.list_files()

        contents = self.get_file_contents(None if file == 'latest' else file)

        log_records = []
        for line in contents.splitlines():
            if not line:
                continue

            level_start = -1
            if '[' in line:
               level_start = line.index('[')

            if level_start > -1:
                log_entry = {}

                dt_str = line[0:level_start]
                try:
                    log_entry['d'] = arrow.get(dt_str).format('YYYY-MM-DD HH:mm:ss.SSS')
                except Exception as e:
                    log_records[-1]['t'] += '\n' + line.strip()
                    continue

                level_end = line.index(']')
                log_entry['l'] = line[level_start + 1: level_end]

                orig_start = line.index('[', level_end)
                orig_end = line.index(']', level_end+1)

                log_entry['o'] = line[orig_start+1:orig_end]

                log_start = line.index(':', orig_end+1)

                log_entry['t'] = line[log_start +1:].strip()
                log_records.append(log_entry)
            else:
                log_records[-1]['t'] += '\n' + line.strip()


        return log_records[::-1][0:limit]
