from copy import deepcopy
import logging
import re
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Generator, Union

from flask import current_app

import flask_openapi.compat.marshmallow as m
from flask_openapi.constants import (
    HTTP_METHODS,
    OAS3_SUB_COMPONENTS,
    OPTIONAL_FIELDS,
    OPTIONAL_OAS3_FIELDS,
)
from flask_openapi.openapi.parsers import (
    extract_definitions,
    extract_schema,
    get_vendor_extension_fields,
    parse_definition_docstring,
    parse_docstring,
)
from flask_openapi.openapi.version import is_openapi3
from flask_openapi.utils.files import get_swag_path_from_doc_dir
from flask_openapi.utils.flask import (
    get_url_mappings,
    has_valid_dispatch_view_docs,
    is_valid_method_view,
)
from flask_openapi.utils.types import ordered_dict_to_dict

from werkzeug.routing import Rule


if TYPE_CHECKING:
    from flask_openapi.core import Swagger

try:
    from flask_mongorest import methods as fmr_methods  # noqa
except ImportError:
    fmr_methods = None


def get_definitions(data: dict, spec: dict) -> dict:
    definitions: dict = extract_schema(data)

    for name, def_model in current_app.swag.get_def_models(
        spec.get("definition_filter")
    ).items():
        description, swag = parse_definition_docstring(
            def_model, current_app.swag.sanitizer
        )

        if name and swag:
            if description:
                swag.update({"description": description})
            definitions[name].update(swag)

    return definitions


def merge_sub_component(dest: dict, key: str, source: dict) -> dict:
    if len(source) > 0 and dest.get(key) is None:
        dest[key] = {}
    if len(source) > 0 and len(dest[key]) >= 0:
        dest[key].update(source)

    return dest


def get_operations(
    swag: dict,
    data: dict,
    spec: dict,
    rule: Rule,
    verb: str,
    optional_fields: list,
    path_verb: str = "",
) -> dict:
    swagger: "Swagger" = current_app.swag

    definitions: dict = get_definitions(data, spec)

    openapi_version: str = swagger.config.get("openapi", "")
    prefix_ids: list = swagger.config.get("prefix_ids", [])
    params: list = swag.get("parameters", [])
    request_body: dict = swag.get("requestBody", {})
    callbacks: dict = swag.get("callbacks", {})
    responses: dict = swag.get("responses", {})

    defs: list = []
    operations: dict = {}
    operation: dict = {}

    if is_openapi3(openapi_version):
        source_components: dict = swag.get("components", {})
        update_schemas: Union[list, dict] = source_components.get("schemas", {})

        # clone list so we can modify
        # schemas are handled separately, so removethem here
        active_sub_components: list[str] = OAS3_SUB_COMPONENTS[:]
        active_sub_components.remove("schemas")

        for subcomponent in OAS3_SUB_COMPONENTS:
            data["components"] = merge_sub_component(
                data["components"],
                subcomponent,
                source_components.get(subcomponent, {}),
            )
    else:
        update_schemas = swag.get("definitions", {})

    if type(update_schemas) == list and type(update_schemas[0]) == dict:
        (update_schemas,) = update_schemas

    definitions.update(update_schemas)

    if verb in swag.keys():
        verb_swag: dict = swag.get(verb, {})
        if len(params) == 0 and verb.lower() in HTTP_METHODS:
            params = verb_swag.get("parameters", [])

    defs += extract_definitions(
        defs,
        endpoint=rule.endpoint,
        verb=verb,
        prefix_ids=prefix_ids,
        openapi_version=openapi_version,
    )
    defs += extract_definitions(
        params,
        endpoint=rule.endpoint,
        verb=verb,
        prefix_ids=prefix_ids,
        openapi_version=openapi_version,
    )

    if request_body:
        content: dict = request_body.get("content", {})
        extract_definitions(
            list(content.values()),
            endpoint=rule.endpoint,
            verb=verb,
            prefix_ids=prefix_ids,
            openapi_version=openapi_version,
        )

    if callbacks:
        callbacks = {str(key): value for key, value in callbacks.items()}
        extract_definitions(
            list(callbacks.values()),
            endpoint=rule.endpoint,
            verb=verb,
            prefix_ids=prefix_ids,
            openapi_version=openapi_version,
        )

    if "responses" in swag:
        responses = {str(key): value for key, value in responses.items()}

        if responses is not None:
            defs += extract_definitions(
                responses.values(),
                endpoint=rule.endpoint,
                verb=verb,
                prefix_ids=prefix_ids,
                openapi_version=openapi_version,
            )

        for definition in defs:
            if "id" not in definition:
                definitions.update(definition)
                continue
            def_id = definition.pop("id")
            if def_id is not None:
                definitions[def_id].update(definition)

    if swag.get("summary"):
        operation["summary"] = swag.get("summary")
    if swag.get("description"):
        operation["description"] = swag.get("description")
    if request_body:
        operation["requestBody"] = request_body
    if callbacks:
        operation["callbacks"] = callbacks
    if responses:
        operation["responses"] = responses
    if len(params) > 0:
        operation["parameters"] = params

    for key in optional_fields:
        if key in swag:
            value = swag.get(key)
            if key in ("produces", "consumes"):
                if not isinstance(value, (list, tuple)):
                    value = [value]

            operation[key] = value

    if path_verb:
        operations[path_verb] = operation
    else:
        operations[verb] = operation

    return operations


def get_specs(
    rules, ignore_verbs, optional_fields, sanitizer, openapi_version, doc_dir=None
):

    specs: list = []
    for rule in rules:
        endpoint = current_app.view_functions[rule.endpoint]
        methods: dict = dict()
        is_mv: bool = is_valid_method_view(endpoint)

        for verb in rule.methods.difference(ignore_verbs):
            if not is_mv and has_valid_dispatch_view_docs(endpoint):
                endpoint.methods = endpoint.methods or ["GET"]
                if verb in endpoint.methods:
                    methods[verb.lower()] = endpoint
            elif getattr(endpoint, "methods", None) is not None:
                if isinstance(endpoint.methods, set):
                    if verb in endpoint.methods:
                        verb = verb.lower()
                        methods[verb] = getattr(endpoint.view_class, verb)
                elif fmr_methods is not None:  # flask-mongorest
                    endpoint_methods: set = set(m.method for m in endpoint.methods)
                    if verb in endpoint_methods:
                        proxy_verb = rule.endpoint.replace(endpoint.__name__, "")
                        if proxy_verb:
                            methods[verb.lower()] = getattr(fmr_methods, proxy_verb)
                else:
                    raise TypeError
            else:
                methods[verb.lower()] = endpoint

        verbs: list = []
        for verb, method in methods.items():

            klass = method.__dict__.get("view_class", None)
            if not is_mv and klass and hasattr(klass, "verb"):
                method = getattr(klass, "verb", None)
            elif klass and hasattr(klass, "dispatch_request"):
                method = getattr(klass, "dispatch_request", None)
            if method is None:  # for MethodView
                method = getattr(klass, verb, None)

            if method is None:
                if is_mv:  # #76 Empty MethodViews
                    continue
                raise RuntimeError("Cannot detect view_func for rule {0}".format(rule))

            swag: dict = {}
            swag_def: dict = {}

            swagged = False

            if getattr(method, "specs_dict", None):
                definition: dict = {}
                merge_specs(
                    swag, m.convert_schemas(deepcopy(method.specs_dict), definition)
                )
                swag_def = definition
                swagged = True

            view_class = getattr(endpoint, "view_class", None)
            if view_class and issubclass(view_class, m.SwaggerView):
                apispec_swag: dict = {}

                # Don't need to alter definitions here
                # Since it only stays in apispec_attrs
                apispec_attrs = optional_fields + [
                    "parameters",
                    "definitions",
                    "responses",
                    "summary",
                    "description",
                ]
                for attr in apispec_attrs:
                    value = getattr(view_class, attr)
                    if value:
                        apispec_swag[attr] = value
                # Don't need to change 'definitions' here
                # Since it would be appended later according to openapi
                apispec_definitions: dict = apispec_swag.get("definitions", {})
                swag.update(m.convert_schemas(apispec_swag, apispec_definitions))
                swag_def = apispec_definitions

                swagged = True

            swag_path = None
            if doc_dir:
                swag_path: str = get_swag_path_from_doc_dir(
                    method, view_class, doc_dir, endpoint
                )

            doc_summary, doc_description, doc_swag = parse_docstring(
                method,
                sanitizer,
                endpoint=rule.endpoint,
                verb=verb,
                swag_path=swag_path,
            )

            if is_openapi3(openapi_version):
                swag.setdefault("components", {})["schemas"] = swag_def
            else:  # openapi2
                swag["definitions"] = swag_def

            if doc_swag:
                merge_specs(swag, doc_swag)
                swagged = True

            if swagged:
                if doc_summary:
                    swag["summary"] = doc_summary

                if doc_description:
                    swag["description"] = doc_description

                verbs.append((verb, swag))

        if verbs:
            specs.append((rule, verbs))

    return specs


def merge_specs(target, source) -> None:
    """
    Update target dictionary with values from the source, recursively.
    List items will be merged.
    """

    for key, value in source.items():
        if isinstance(value, dict):
            node = target.setdefault(key, {})
            merge_specs(node, value)
        elif isinstance(value, list):
            node = target.setdefault(key, [])
            node.extend(value)
        else:
            target[key] = value


def get_schema_specs(schema_id, swagger) -> Any:
    ignore_verbs = set(swagger.config.get("ignore_verbs", ("HEAD", "OPTIONS")))

    # technically only responses is non-optional
    optional_fields: list[str] = (
        swagger.config.get("optional_fields") or OPTIONAL_FIELDS
    )

    openapi_version = swagger.config.get("openapi")

    with swagger.app.app_context():
        specs = get_specs(
            current_app.url_map.iter_rules(),
            ignore_verbs,
            optional_fields,
            swagger.sanitizer,
            openapi_version,
        )

        swags: Generator = (
            swag for _, verbs in specs for _, swag in verbs if swag is not None
        )

    for swag in swags:
        for d in swag.get("parameters", []):
            d_schema_id = d.get("schema", {}).get("id")
            if d_schema_id is not None and d_schema_id.lower() == schema_id.lower():
                return swag


def apispec_to_template(app, spec, definitions=None, paths=None) -> dict:
    """
    Converts apispec object in to flasgger definitions template
    :param app: Current app
    :param spec: apispec.APISpec
    :param definitions: a list of [Schema, ..] or [('Name', Schema), ..]
    :param paths: A list of flask views
    """
    definitions = definitions or []
    paths = paths or []

    with app.app_context():
        for definition in definitions:
            if isinstance(definition, (tuple, list)):
                name, schema = definition
            else:
                schema = definition
                name = schema.__name__.replace("Schema", "")

            spec.components.schema(name, schema=schema)

        for path in paths:
            spec.path(view=path)

    spec_dict = spec.to_dict()
    ret: dict = ordered_dict_to_dict(spec_dict)
    return ret


def get_apispecs(endpoint: str = "apispec_1") -> dict:
    swagger: "Swagger" = current_app.swag
    spec: dict = {}
    openapi_version: str = swagger.config.get("openapi", "")
    ignore_verbs: set[str] = set(
        swagger.config.get("ignore_verbs", ("HEAD", "OPTIONS"))
    )
    optional_fields: list = swagger.config.get("optional_fields") or OPTIONAL_FIELDS
    operations: dict = {}
    specs: list = get_specs(
        get_url_mappings(spec.get("rule_filter")),
        ignore_verbs,
        optional_fields,
        swagger.sanitizer,
        openapi_version,
        doc_dir=swagger.config.get("doc_dir"),
    )

    if not current_app.debug and endpoint in swagger.apispecs:
        return swagger.apispecs[endpoint]

    for configured_spec in swagger.config["specs"]:
        if configured_spec["endpoint"] == endpoint:
            spec = configured_spec
            break

    if not spec:
        raise RuntimeError(
            f"Can't find specs by endpoint {endpoint}, check your config"
        )

    data: dict = {
        "info": swagger.config.get("info") or {
            "version": spec.get("version", swagger.config.get("version", "0.0.1")),
            "title": spec.get("title", swagger.config.get("title", "A swagger API")),
            "description": spec.get(
                "description", swagger.config.get("description", "")
            ),
            "termsOfService": spec.get(
                "termsOfService", swagger.config.get("termsOfService", "/tos")
            ),
        },
        "paths": swagger.config.get("paths") or defaultdict(dict),
        "definitions": swagger.config.get("definitions") or defaultdict(dict),
    }

    if openapi_version:
        data["openapi"] = openapi_version
    else:
        data["swagger"] = swagger.config.get("swagger") or swagger.config.get(
            "swagger_version", "2.0"
        )

    # If it's openapi3, #/components/schemas replaces #/definitions
    if is_openapi3(openapi_version):
        optional_oas3_fields: list = (
            swagger.config.get("optional_oas3_fields") or OPTIONAL_OAS3_FIELDS
        )

        data.setdefault("components", {})["schemas"] = data["definitions"]

        for key in optional_oas3_fields:
            if swagger.config.get(key):
                data[key] = swagger.config.get(key)

    # Support extension properties in the top level config
    top_level_extension_options: dict = get_vendor_extension_fields(swagger.config)

    if top_level_extension_options:
        data.update(top_level_extension_options)

    # if True schemaa ids will be prefized by function_method_{id}
    # for backwards compatibility with <= 0.5.14

    if swagger.config.get("host"):
        data["host"] = swagger.config.get("host")
    if swagger.config.get("basePath"):
        data["basePath"] = swagger.config.get("basePath")
    if swagger.config.get("schemes"):
        data["schemes"] = swagger.config.get("schemes")
    if swagger.config.get("securityDefinitions"):
        data["securityDefinitions"] = swagger.config.get("securityDefinitions")

    # set defaults from template
    if swagger.template is not None:
        data.update(swagger.template)

    for rule, verbs in specs:
        for verb, swag in verbs:
            if swag.get("paths"):
                try:
                    # /projects/{project_id}/alarms:
                    for path in swag.get("paths"):
                        # get:
                        for path_verb in swag.get("paths").get(path):
                            if path_verb == verb:
                                operations = get_operations(
                                    swag.get("paths").get(path).get(path_verb),
                                    data,
                                    spec,
                                    rule,
                                    verb,
                                    optional_fields,
                                    path_verb,
                                )
                except AttributeError:
                    logging.exception(
                        f"Swagger doc not in the correct format. {swagger}"
                    )
            else:
                operations = get_operations(
                    swag, data, spec, rule, verb, optional_fields
                )

        if operations:
            srule: str = f"{swagger.template.get('swaggerUiPrefix', '')}{rule}"
            base_path: str = swagger.template.get("basePath", "None")

            if base_path:
                if base_path.endswith("/"):
                    base_path = base_path[:-1]
                if base_path:
                    if srule.startswith(base_path):
                        srule = srule[len(base_path) :]

            for arg in re.findall("(<([^<>]*:)?([^<>]*)>)", srule):
                srule = srule.replace(arg[0], "{%s}" % arg[2])

            for key, val in operations.items():
                if srule not in data["paths"]:
                    data["paths"][srule] = {}
                if key in data["paths"][srule]:
                    data["paths"][srule][key].update(val)
                else:
                    data["paths"][srule][key] = val

    swagger.apispecs[endpoint] = data

    if is_openapi3(openapi_version):
        del data["definitions"]

    return data
