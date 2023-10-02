# Flask-OpenAPI3-UI

[![Python](https://img.shields.io/badge/python-3.6.1-blue.svg)](https://img.shields.io/badge/python-3.6.1-blue.svg)
[![PyPi](https://img.shields.io/pypi/v/Flask-OpenAPI3-UI.svg)](https://pypi.python.org/pypi/Flask-OpenAPI3-UI)
[![PyPi](https://img.shields.io/pypi/dm/Flask-OpenAPI3-UI.svg)](https://pypi.python.org/pypi/Flask-OpenAPI3-UI)
[![Flask-OpenAPI3-UI](https://snyk.io/advisor/python/Flask-OpenAPI3-UI/badge.svg)](https://snyk.io/advisor/python/Flask-OpenAPI3-UI)

Next generation OpenAPI v3 Integration for Flask based APIs. Based on Flasgger.

## Install
```
pip install Flask-OpenAPI3-UI
```

## Usage
You can start your Swagger spec with any default data providing a template:
```python
from flask_openapi import Swagger

def main():
  app = create_app()
  app.config['SWAGGER'] = {
      "uiversion": 3,
      "openapi": "3.0.3",
      "info": {
          "title": "API documentation",
          "description": "API docs for ",
          "version": 1.0.0
      },
      "swagger_ui": True,
      "basePath": "/api",  # base bash for blueprint registration
      "components": {
          "securitySchemes": {
              "bearerAuth": {
                  "type": "http",
                  "scheme": "bearer",
                  "bearerFormat": "JWT"
              }
          }
      },
      "title": "API docs",
      "optional_fields": ["components", "tags", "paths"],
      "doc_dir": "/home/admin/flaskapp/src/api/",
  }
  Swagger(app=app)
```
And then the template is the default data unless some view changes it. You can also provide all your specs as template and have no views. Or views in external APP.
