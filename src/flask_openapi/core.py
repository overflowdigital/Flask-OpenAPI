"""
What's the big idea?

An endpoint that traverses all restful endpoints producing a swagger 2.0 schema
If a swagger yaml description is found in the docstrings for an endpoint
we add the endpoint to swagger specification output

"""
from collections import defaultdict
from functools import partial, wraps
from typing import Any, Callable, Optional

from flask import Blueprint, Flask, abort, redirect, request, url_for

from flask_openapi.constants import DEFAULT_CONFIG
from flask_openapi.openapi.file import load_swagger_file
from flask_openapi.openapi.parsers import extract_schema
from flask_openapi.openapi.specs import get_apispecs, get_schema_specs
from flask_openapi.openapi.validator import validate
from flask_openapi.openapi.version import is_openapi3
from flask_openapi.utils.decorators import swag_annotation
from flask_openapi.utils.sanitizers import BR_SANITIZER
from flask_openapi.views.docs import APIDocsView
from flask_openapi.views.oauth import OAuthRedirect
from flask_openapi.views.specs import APISpecsView

import jsonschema


try:
    from flask_restful.reqparse import RequestParser
except ImportError:
    RequestParser = None


class SwaggerDefinition:
    """
    Class based definition
    """

    def __init__(self, name: str, obj: dict, tags: Optional[list[str]] = None) -> None:
        self.name: str = name
        self.obj: dict = obj
        self.tags: list[str] = tags or []


class Swagger:
    def __init__(
        self,
        app: Flask = None,
        config: dict = {},
        sanitizer: Optional[Callable] = None,
        template: dict = {},
        template_file: str = "",
        decorators: Optional[list] = None,
        validation_function: Optional[Callable] = None,
        validation_error_handler: Optional[Callable] = None,
        parse: bool = False,
        format_checker: Optional[Callable] = None,
        merge: bool = False,
    ) -> None:
        self._configured: bool = False
        self.endpoints: list[str] = []
        self.definition_models: list = []
        self.sanitizer: Callable = sanitizer or BR_SANITIZER

        if config and merge:
            self.config: dict = dict(DEFAULT_CONFIG.copy(), **config)
        elif config and not merge:
            self.config = config
        elif not config:
            self.config = DEFAULT_CONFIG.copy()
        else:  # The above branches must be exhaustive
            raise ValueError

        self.template: dict = template
        self.template_file: str = template_file
        self.decorators: list | None = decorators
        self.format_checker: Callable = format_checker or jsonschema.FormatChecker()

        self.default_validation_function: Callable = (
            lambda data, schema: jsonschema.validate(
                data, schema, format_checker=self.format_checker
            )
        )
        self.default_error_handler: Callable = lambda error, _, __: abort(
            400, error.message
        )

        self.validation_function: Callable = (
            validation_function or self.default_validation_function
        )
        self.validation_error_handler: Callable = (
            validation_error_handler or self.default_error_handler
        )
        self.apispecs: dict[str, dict] = {}  # cached apispecs
        self.parse: bool = parse

        if app:
            self.init_app(app)

    def init_app(self, app: Flask, decorators: list = None) -> None:
        """Initialize the app with Swagger plugin"""
        self.decorators = decorators or self.decorators
        self.app: Flask = app
        self.app.add_url_rule = swag_annotation(self.app.add_url_rule)  # type: ignore

        self.load_config(app)

        if self.template_file:
            self.template = load_swagger_file(app, self.template_file)

        self.register_views(app)
        self.add_headers(app)

        if self.parse:  # type: ignore
            if RequestParser is None:
                raise RuntimeError("Please install flask_restful")
            self.parsers: dict = {}
            self.schemas: dict = {}
            self.parse_request(app)

        self._configured = True
        app.swag = self

    @property
    def configured(self) -> bool:
        """
        Return if `init_app` is configured
        """
        return self._configured

    def get_def_models(self, definition_filter: Optional[Callable] = None) -> dict:
        """Used for class based definitions"""
        definition_filter = definition_filter or (lambda tag: True)
        return {
            definition.name: definition.obj
            for definition in self.definition_models
            if definition_filter(definition)
        }

    def definition(self, name, tags=None) -> Callable:
        """
        Decorator to add class based definitions
        """

        def wrapper(obj):
            self.definition_models.append(SwaggerDefinition(name, obj, tags=tags))
            return obj

        return wrapper

    def load_config(self, app) -> None:
        """
        Copy config from app
        """
        self.config.update(app.config.get("SWAGGER", {}))

    def register_views(self, app) -> None:
        """
        Register views
        """

        # Wrap the views in an arbitrary number of decorators.
        def wrap_view(view):
            if self.decorators:
                for decorator in self.decorators:
                    view = decorator(view)
            return view

        if self.config.get("swagger_ui", True):
            uiversion: int = self.config.get("uiversion", 3)
            blueprint: Blueprint = Blueprint(
                self.config.get("endpoint", "flask_openapi"),
                __name__,
                url_prefix=self.config.get("url_prefix", None),
                subdomain=self.config.get("subdomain", None),
                template_folder=self.config.get(
                    "template_folder", "swagger_ui/v{0}/templates".format(uiversion)
                ),
                static_folder=self.config.get(
                    "static_folder", "swagger_ui/v{0}/static".format(uiversion)
                ),
                static_url_path=self.config.get("static_url_path", None),
            )

            specs_route: str = self.config.get("specs_route", "/apidocs/")
            blueprint.add_url_rule(
                specs_route,
                "apidocs",
                view_func=wrap_view(
                    APIDocsView().as_view("apidocs", view_args=dict(config=self.config))
                ),
            )

            if uiversion < 3:
                redirect_default: str = specs_route + "/o2c.html"
            else:
                redirect_default = "/oauth2-redirect.html"

            blueprint.add_url_rule(
                self.config.get("oauth_redirect", redirect_default),
                "oauth_redirect",
                view_func=wrap_view(OAuthRedirect().as_view("oauth_redirect")),
            )

            # backwards compatibility with old url style
            blueprint.add_url_rule(
                "/apidocs/index.html",
                view_func=lambda: redirect(url_for("flask_openapi.apidocs")),
            )
        else:
            blueprint = Blueprint(
                self.config.get("endpoint", "flask_openapi"), __name__
            )

        for spec in self.config["specs"]:
            self.endpoints.append(spec["endpoint"])
            blueprint.add_url_rule(
                spec["route"],
                spec["endpoint"],
                view_func=wrap_view(
                    APISpecsView.as_view(
                        spec["endpoint"],
                        loader=partial(get_apispecs, endpoint=spec["endpoint"]),
                    )
                ),
            )
        app.register_blueprint(blueprint)

    def add_headers(self, app) -> None:
        """
        Inject headers after request
        """

        @app.after_request
        def after_request(response):  # noqa
            for header, value in self.config.get("headers", []):
                response.headers[header] = value
            return response

    def parse_request(self, app) -> None:
        @app.before_request
        def before_request() -> None:  # noqa
            """
            Parse and validate request data(query, form, header and body),
            set data to `request.parsed_data`
            """
            # convert "/api/items/<int:id>/" to "/api/items/{id}/"
            subs: list = []
            for sub in str(request.url_rule).split("/"):
                if "<" in sub:
                    if ":" in sub:
                        start: int = sub.index(":") + 1
                    else:
                        start = 1
                    subs.append("{{{:s}}}".format(sub[start:-1]))
                else:
                    subs.append(sub)
            path = "/".join(subs)
            path_key: str = path + request.method.lower()

            if not self.app.debug and path_key in self.parsers:
                parsers = self.parsers[path_key]
                schemas = self.schemas[path_key]
            else:
                doc = None
                definitions = None
                for spec in self.config["specs"]:
                    apispec: dict = get_apispecs(endpoint=spec["endpoint"])
                    if path in apispec["paths"]:
                        if request.method.lower() in apispec["paths"][path]:
                            doc = apispec["paths"][path][request.method.lower()]
                            definitions = extract_schema(apispec)
                            break
                if not doc:
                    return

                parsers = defaultdict(RequestParser)
                schemas = defaultdict(
                    lambda: {"type": "object", "properties": defaultdict(dict)}
                )
                self.update_schemas_parsers(doc, schemas, parsers, definitions)
                self.schemas[path_key] = schemas
                self.parsers[path_key] = parsers

            parsed_data: dict[str, dict[str, Any]] = {"path": request.view_args or {}}
            for location in parsers.keys():
                parsed_data[location] = parsers[location].parse_args()
            if "json" in schemas:
                parsed_data["json"] = request.json or {}
            for location, data in parsed_data.items():
                try:
                    self.validation_function(data, schemas[location])
                except jsonschema.ValidationError as e:
                    self.validation_error_handler(e, data, schemas[location])

            setattr(request, "parsed_data", parsed_data)  # noqa

    def update_schemas_parsers(self, doc, schemas, parsers, definitions) -> None:
        """
        Schemas and parsers would be updated here from doc
        """
        if is_openapi3(self.config.get("openapi", "")):
            # 'json' to comply with self.SCHEMA_LOCATIONS's {'body':'json'}
            location = "json"
            json_schema = None

            # For openapi3, currently only support single schema
            for name, value in doc.get("requestBody", {}).get("content", {}).items():
                if "application/json" in name:
                    # `$ref` to json, lookup in #/components/schema
                    json_schema = value.get("schema", {})
                else:  # schema set in requesty body
                    # Since osa3 might changed, repeat openapi2's code
                    parsers[location].add_argument(
                        name,
                        type=self.SCHEMA_TYPES[
                            value["schema"].get("type", None)
                            if "schema" in value
                            else value.get("type", None)
                        ],
                        required=value.get("required", False),
                        # Parsed in body
                        location=self.SCHEMA_LOCATIONS["body"],
                        store_missing=False,
                    )

            # TODO support anyOf and oneOf in the future
            if (json_schema is not None) and isinstance(json_schema, dict):

                schemas[location] = json_schema
                self.set_schemas(schemas, location, definitions)

        else:  # openapi2
            for param in doc.get("parameters", []):
                location = self.SCHEMA_LOCATIONS[param["in"]]
                if location == "json":  # load data from 'request.json'
                    schemas[location] = param["schema"]
                    self.set_schemas(schemas, location, definitions)
                else:
                    name = param["name"]
                    if location != "path":
                        parsers[location].add_argument(
                            name,
                            type=self.SCHEMA_TYPES[
                                param["schema"].get("type", None)
                                if "schema" in param
                                else param.get("type", None)
                            ],
                            required=param.get("required", False),
                            location=self.SCHEMA_LOCATIONS[param["in"]],
                            store_missing=False,
                        )

                    for k in param:
                        if k != "required":
                            schemas[location]["properties"][name][k] = param[k]

    def set_schemas(self, schemas: dict, location: str, definitions: dict) -> None:
        if is_openapi3(self.config.get("openapi")):
            schemas[location]["components"] = {"schemas": dict(definitions)}
        else:
            schemas[location]["definitions"] = dict(definitions)

    def validate(
        self, schema_id, validation_function=None, validation_error_handler=None
    ) -> Callable:
        """
        A decorator that is used to validate incoming requests data
        against a schema

            swagger = Swagger(app)

            @app.route('/pets', methods=['POST'])
            @swagger.validate('Pet')
            @swag_from("pet_post_endpoint.yml")
            def post():
                return db.insert(request.data)

        This annotation only works if the endpoint is already swagged,
        i.e. placing @swag_from above @validate or not declaring the
        swagger specifications in the method's docstring *won't work*

        Naturally, if you use @app.route annotation it still needs to
        be the outermost annotation

        :param schema_id: the id of the schema with which the data will
            be validated

        :param validation_function: custom validation function which
            takes the positional arguments: data to be validated at
            first and schema to validate against at second

        :param validation_error_handler: custom function to handle
            exceptions thrown when validating which takes the exception
            thrown as the first, the data being validated as the second
            and the schema being used to validate as the third argument
        """

        if validation_function is None:
            validation_function = self.validation_function

        if validation_error_handler is None:
            validation_error_handler = self.validation_error_handler

        def decorator(func) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                specs = get_schema_specs(schema_id, self)
                validate(
                    schema_id=schema_id,
                    specs=specs,
                    validation_function=validation_function,
                    validation_error_handler=validation_error_handler,
                    openapi_version=self.config.get("openapi"),
                )
                return func(*args, **kwargs)

            return wrapper

        return decorator

    def get_schema(self, schema_id):
        """
        This method finds a schema known to Flasgger and returns it.

        :raise KeyError: when the specified :param schema_id: is not
        found by Flasgger

        :param schema_id: the id of the desired schema
        """
        schema_specs = get_schema_specs(schema_id, self)

        if schema_specs is None:
            raise KeyError("Specified schema_id '{0}' not found".format(schema_id))

        for schema in (
            parameter.get("schema") for parameter in schema_specs["parameters"]
        ):
            if schema is not None and schema.get("id").lower() == schema_id:
                return schema

    def is_openapi3(self) -> bool:
        return is_openapi3(self.config.get("openapi"))


# backwards compatibility
Flasgger = Swagger  # noqa
OpenAPI = Swagger  # noqa
