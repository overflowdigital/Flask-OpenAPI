from flask import current_app, url_for

OPTIONAL_FIELDS = [
    'tags',
    'consumes',
    'produces',
    'schemes',
    'security',
    'deprecated',
    'operationId',
    'externalDocs'
]

OPTIONAL_OAS3_FIELDS = [
    'components',
    'servers'
]

OAS3_SUB_COMPONENTS = [
    "parameters",
    "securitySchemes",
    "requestBodies",
    "responses",
    "headers",
    "examples",
    "links",
    "callbacks",
    "schemas"
]

DEFAULT_FIELDS = {
    "tags": [],
    "consumes": ['application/json'],
    "produces": ['application/json'],
    "schemes": [],
    "security": [],
    "deprecated": False,
    "operationId": "",
    "definitions": {},
    "responses": {},
    "summary": None,
    "description": None,
    "parameters": []
}

with current_app.context:
    DEFAULT_FAVICON = url_for('flask_openapi.static', filename='favicon-32x32.png')
    DEFAULT_BUNDLE_JS = url_for('flask_openapi.static', filename='swagger-ui-bundle.js')
    DEFAULT_PRESET_JS = url_for('flask_openapi.static', filename='swagger-ui-standalone-preset.js')
    DEFAULT_JQUERY = url_for('flask_openapi.static', filename='lib/jquery.min.js')
    DEFAULT_CSS = url_for('flask_openapi.static', filename='swagger-ui.css')

DEFAULT_ENDPOINT = 'apispec_1'

DEFAULT_CONFIG = {
    "headers": [],
    "specs": [
        {
            "endpoint": DEFAULT_ENDPOINT,
            "route": '/{}.json'.format(DEFAULT_ENDPOINT),
            "rule_filter": lambda rule: True,  # all in
            "model_filter": lambda tag: True,  # all in
        }
    ],
    "static_url_path": "/flask_openapi_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/"
}

SCHEMA_TYPES = {
    'string': str,
    'integer': int,
    'number': float,
    'boolean': bool
}

SCHEMA_LOCATIONS = {
    'query': 'args',
    'header': 'headers',
    'formData': 'form',
    'body': 'json',
    'path': 'path'
}

HTTP_METHODS = [
    'get',
    'post',
    'put',
    'delete',
    'patch'
]
