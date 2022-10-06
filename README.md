# Flask-OpenAPI3-UI

Flask-OpenAPI3 is a Flask extension for creating a OpenAPI3 specification from an applications endpoints and displays that with a customisable UI based on SwaggerUI. Based on Flasgger.

## Quick Start
`pip3 install Flask-OpenAPI3-UI`

Create a `main.py` like so:
```python
from flask import Flask, jsonify
from flask.views import MethodView

from flask_openapi import OpenAPI, spec_from


class MyView(MethodView):
    @use_spec('MyView_Get.yml')
    def get(self):
        return jsonify(msg='Hello World')

if __name__ == '__main__':
    app = Flask(__name__)
    app.add_url_rule('/api', view_func=MyView.as_view('my_view')
```

And then a sample yml file called `MyView_Get.yml`:
```yml

```
