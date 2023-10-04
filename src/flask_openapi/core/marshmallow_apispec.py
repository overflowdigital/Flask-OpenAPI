# coding: utf-8
import inspect
from typing import Any, Callable, Optional

from flask import Flask
from flask.views import MethodView
from flask_openapi.core.validation import validate
from flask_openapi.utils.constants import OPTIONAL_FIELDS

try:
    import marshmallow
    from apispec import APISpec as BaseAPISpec
    from apispec.ext.marshmallow import openapi
    from marshmallow import fields  # noqa

    openapi_converter: openapi.OpenAPIConverter = openapi.OpenAPIConverter(
        openapi_version="2.0",
        schema_name_resolver=lambda schema: None,
        spec=BaseAPISpec,  # type: ignore
    )
    schema2jsonschema = openapi_converter.schema2jsonschema
    schema2parameters = openapi_converter.schema2parameters

    class Schema(marshmallow.Schema):
        swag_in: str = "body"
        swag_validate: bool = True
        swag_validation_function: Optional[Callable] = None
        swag_validation_error_handler: Optional[Callable] = None
        swag_require_data: bool = True

        def to_specs_dict(self) -> dict[str, type["Schema"]]:
            specs = {"parameters": self.__class__}
            definitions: dict = {}
            specs.update(convert_schemas(specs, definitions))
            specs["definitions"] = definitions  # type: ignore
            return specs

except ImportError:
    Schema = None  # type: ignore
    fields = None  # type: ignore
    schema2jsonschema = lambda schema: {}  # type: ignore  # noqa
    schema2parameters = lambda schema, location: []  # type: ignore  # noqa
    BaseAPISpec = object  # type: ignore


class APISpec(BaseAPISpec):
    """
    Wrapper around APISpec to add `to_flasgger` method
    """

    def to_flasgger(
        self,
        app: Optional[Flask] = None,
        definitions: Optional[list] = None,
        paths: Optional[list] = None,
    ) -> dict:
        """
        Converts APISpec dict to flasgger suitable dict
        also adds definitions and paths (optional)

        :param app: Flask app
        :type app: Flask

        :param definitions: a list of [Schema, ..] or [('Name', Schema), ..]
        :type definitions: list

        :param paths: A list of flask views
        :type paths: list

        :return: Flasgger suitable dict
        :rtype: dict
        """
        if Schema is None:
            raise RuntimeError("Please install marshmallow and apispec")

        from flask_openapi.core.specs import apispec_to_template

        return apispec_to_template(app, self, definitions=definitions, paths=paths)


class SwaggerView(MethodView):
    """
    A Swagger view
    """

    parameters: list = []
    responses: dict = {}
    definitions: dict = {}
    tags: list = []
    consumes: list[str] = ["application/json"]
    produces: list[str] = ["application/json"]
    schemes: list = []
    security: list = []
    deprecated: bool = False
    operationId: Optional[Any] = None
    externalDocs: dict = {}
    summary: Optional[Any] = None
    description: Optional[str] = None
    validation: bool = False
    validation_function: Optional[Callable] = None
    validation_error_handler: Optional[Callable] = None

    def dispatch_request(self, *args, **kwargs):
        """
        If validation=True perform validation
        """
        if self.validation:
            specs: dict = {}
            attrs: list[str] = OPTIONAL_FIELDS + [
                "parameters",
                "definitions",
                "responses",
                "summary",
                "description",
            ]
            for attr in attrs:
                specs[attr] = getattr(self, attr)
            definitions: dict = {}
            specs.update(convert_schemas(specs, definitions))
            specs["definitions"] = definitions
            validate(
                specs=specs,
                validation_function=self.validation_function,
                validation_error_handler=self.validation_error_handler,
            )
        return super(SwaggerView, self).dispatch_request(*args, **kwargs)


def convert_schemas(d: dict, definitions: dict = {}) -> dict:
    """
    Convert Marshmallow schemas to dict definitions

    Also updates the optional definitions argument with any definitions
    entries contained within the schema.

    :param d: dict to convert
    :type d: dict

    :param definitions: dict of definitions
    :type definitions: dict

    :return: converted dict
    :rtype: dict
    """
    definitions.update(d.get("definitions", {}))
    new: dict = {}

    for k, v in d.items():
        if isinstance(v, dict):
            v = convert_schemas(v, definitions)
        if isinstance(v, (list, tuple)):
            new_v: list = []
            for item in v:
                if isinstance(item, dict):
                    new_v.append(convert_schemas(item, definitions))
                else:
                    new_v.append(item)
            v = new_v
        if inspect.isclass(v) and issubclass(v, Schema):
            if Schema is None:
                raise RuntimeError("Please install marshmallow and apispec")

            definitions[v.__name__] = schema2jsonschema(v)
            ref: dict[str, str] = {"$ref": "#/definitions/{0}".format(v.__name__)}
            if k == "parameters":
                new[k] = schema2parameters(v, location=v.swag_in)
                new[k][0]["schema"] = ref
                if len(definitions[v.__name__]["required"]) != 0:
                    new[k][0]["required"] = True
            else:
                new[k] = ref
        else:
            new[k] = v

    # This key is not permitted anywhere except the very top level.
    if "definitions" in new:
        del new["definitions"]

    return new
