from enum import Enum
from json import JSONEncoder

from datetime import datetime

from Bot.Target import Target
from Bot.Value import Value


class CustomJsonEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Value):
            return str(obj)
        if isinstance(obj, Target):
            return obj.to_json_dict()
        if isinstance(obj, float):
            return format(obj, '.8f')
        if isinstance(obj, Enum):
            return obj.name
        if isinstance(obj, datetime):
            return obj.now().replace(microsecond=0).isoformat(' ')
        return obj.__dict__
