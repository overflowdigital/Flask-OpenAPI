# coding: utf-8
import inspect
from typing import Optional, cast

from flask import Flask
from flask import typing as ft
from flask.views import MethodView

from flask_openapi.constants import OPTIONAL_FIELDS
from flask_openapi.utils import apispec_to_template, validate

try:
    from apispec import APISpec as BaseAPISpec
    from apispec.ext.marshmallow import openapi
    from marshmallow.schema import Schema as MarshmallowSchema

    openapi_converter = openapi.OpenAPIConverter(
        openapi_version='2.0',
        schema_name_resolver=lambda schema: None,
        spec=cast(BaseAPISpec, BaseAPISpec)  # mypy man...
    )

    schema2jsonschema = openapi_converter.schema2jsonschema
    schema2parameters = openapi_converter.schema2parameters

    class Schema(MarshmallowSchema):
        swag_in = "body"
        swag_validate = True
        swag_validation_function = None
        swag_validation_error_handler = None
        swag_require_data = True

        def to_specs_dict(self) -> dict:
            specs: dict = {'parameters': self.__class__}
            definitions: dict = {}
            specs.update(convert_schemas(specs, definitions))
            specs['definitions'] = definitions
            return specs

except ImportError:
    Schema = None  # type: ignore

    def schema2jsonschema(schema): return {}  # type: ignore # noqa
    def schema2parameters(schema, location): return []  # type: ignore # noqa

    BaseAPISpec = object  # type: ignore


class APISpec(BaseAPISpec):
    """
    Wrapper around APISpec to add `to_swagger` method
    """

    def to_swagger(self, app: Optional[Flask] = None, definitions: Optional[dict] = None, paths: Optional[list] = None) -> dict:
        """
        Converts APISpec dict to swagger suitable dict
        also adds definitions and paths (optional)
        """
        if Schema is None:
            raise RuntimeError('Please install marshmallow and apispec')

        return apispec_to_template(
            app,
            self,
            definitions=definitions,
            paths=paths
        )


class SwaggerView(MethodView):
    """
    A Swagger view
    """
    parameters: list = []
    responses: dict = {}
    definitions: dict = {}
    tags: list = []
    consumes = ['application/json']
    produces = ['application/json']
    schemes: list = []
    security: list = []
    deprecated = False
    operationId = None
    externalDocs: dict = {}
    summary = None
    description = None
    validation = False
    validation_function = None
    validation_error_handler = None

    def dispatch_request(self, *args: tuple, **kwargs: dict) -> ft.ResponseReturnValue:
        """
        If validation=True perform validation
        """
        if self.validation:
            specs: dict = {}
            attrs: list = OPTIONAL_FIELDS + [
                'parameters', 'definitions', 'responses',
                'summary', 'description'
            ]
            for attr in attrs:
                specs[attr] = getattr(self, attr)
            definitions: dict = {}
            specs.update(convert_schemas(specs, definitions))
            specs['definitions'] = definitions

            validate(
                specs=specs, validation_function=self.validation_function,
                validation_error_handler=self.validation_error_handler
            )
        return super(SwaggerView, self).dispatch_request(*args, **kwargs)


def convert_schemas(d: dict, definitions: Optional[dict] = None) -> dict:
    """
    Convert Marshmallow schemas to dict definitions

    Also updates the optional definitions argument with any definitions
    entries contained within the schema.
    """
    if definitions is None:
        definitions = {}

    definitions.update(d.get('definitions', {}))

    new = {}

    for k, v in d.items():
        if isinstance(v, dict):
            v = convert_schemas(v, definitions)
        if isinstance(v, (list, tuple)):
            new_v = []
            for item in v:
                if isinstance(item, dict):
                    new_v.append(convert_schemas(item, definitions))
                else:
                    new_v.append(item)
            v = new_v
        if inspect.isclass(v) and issubclass(v, Schema):

            if Schema is None:
                raise RuntimeError('Please install marshmallow and apispec')

            definitions[v.__name__] = schema2jsonschema(v)
            ref = {
                "$ref": "#/definitions/{0}".format(v.__name__)
            }
            if k == 'parameters':
                new[k] = schema2parameters(v, location=v.swag_in)
                new[k][0]['schema'] = ref
                if len(definitions[v.__name__]['required']) != 0:
                    new[k][0]['required'] = True
            else:
                new[k] = ref
        else:
            new[k] = v

    # This key is not permitted anywhere except the very top level.
    if 'definitions' in new:
        del new['definitions']

    return new
