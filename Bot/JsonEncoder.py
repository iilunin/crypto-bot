from enum import Enum
from json import JSONEncoder

from Bot.Target import Target
from Bot.Value import Value


class CustomJsonEncoder(JSONEncoder):
    def default(self, obj):
        print(type(obj))
        if isinstance(obj, Value):
            return str(obj)
        if isinstance(obj, Target):
            return obj.to_json_dict()
        if isinstance(obj, float):
            return format(obj, '.8f')
        if isinstance(obj, Enum):
            return obj.name
        return obj.__dict__
