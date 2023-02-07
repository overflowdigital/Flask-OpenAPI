OPTIONAL_FIELDS: list[str] = [
    "tags",
    "consumes",
    "produces",
    "schemes",
    "security",
    "deprecated",
    "operationId",
    "externalDocs",
]

OPTIONAL_OAS3_FIELDS: list[str] = ["components", "servers"]

OAS3_SUB_COMPONENTS: list[str] = [
    "parameters",
    "securitySchemes",
    "requestBodies",
    "responses",
    "headers",
    "examples",
    "links",
    "callbacks",
    "schemas",
]

DEFAULT_FIELDS: dict = {
    "tags": [],
    "consumes": ["application/json"],
    "produces": ["application/json"],
    "schemes": [],
    "security": [],
    "deprecated": False,
    "operationId": "",
    "definitions": {},
    "responses": {},
    "summary": None,
    "description": None,
    "parameters": [],
}

DEFAULT_FAVICON = "favicon-32x32.png"

DEFAULT_BUNDLE_JS = "swagger-ui-bundle.js"

DEFAULT_PRESET_JS = "swagger-ui-standalone-preset.js"

DEFAULT_JQUERY = "lib/jquery.min.js"

DEFAULT_CSS = "swagger-ui.css"

DEFAULT_ENDPOINT = "apispec_1"

DEFAULT_CONFIG: dict = {
    "headers": [],
    "specs": [
        {
            "endpoint": DEFAULT_ENDPOINT,
            "route": "/{}.json".format(DEFAULT_ENDPOINT),
            "rule_filter": lambda rule: True,  # all in
            "model_filter": lambda tag: True,  # all in
        }
    ],
    "static_url_path": "/flask_openapi_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/",
}

SCHEMA_TYPES: dict = {"string": str, "integer": int, "number": float, "boolean": bool}

SCHEMA_LOCATIONS: dict[str, str] = {
    "query": "args",
    "header": "headers",
    "formData": "form",
    "body": "json",
    "path": "path",
}

HTTP_METHODS: list[str] = ["get", "post", "put", "delete", "patch"]
