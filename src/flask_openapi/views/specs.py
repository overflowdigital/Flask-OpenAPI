import json
from typing import Any, Callable

from flask import Response, jsonify
from flask.views import MethodView


class APISpecsView(MethodView):
    """View that loads the JSON file of compiled api specs"""

    def __init__(self, *args: tuple, **kwargs: dict[str, Any]) -> None:
        self.loader: Callable = kwargs.pop('loader')  # type: ignore
        super(APISpecsView, self).__init__(*args, **kwargs)

    def get(self) -> Response:
        try:
            return jsonify(self.loader())
        except Exception:
            specs: str = json.dumps(self.loader())
            return Response(specs, mimetype="application/json")
