from json import JSONEncoder

from flask_openapi.utils.types import LazyString


class LazyJSONEncoder(JSONEncoder):
    def default(self, obj) -> str:
        if isinstance(obj, LazyString):
            return str(obj)
        return super(LazyJSONEncoder, self).default(obj)
