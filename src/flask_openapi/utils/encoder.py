from flask import JSONEncoder

from flask_openapi.utils.types import LazyString


class LazyJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, LazyString):
            return str(obj)
        return super(LazyJSONEncoder, self).default(obj)
