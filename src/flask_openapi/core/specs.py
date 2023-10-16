from copy import deepcopy
from typing import Any, Callable, Iterator, Optional, Union, Dict, Set, List

from flask import current_app
from flask_openapi.core.marshmallow_apispec import convert_schemas, SwaggerView
from flask_openapi.core.parser import parse_docstring
from flask_openapi.utils.constants import OPTIONAL_FIELDS
from flask_openapi.utils.paths import get_swag_path_from_doc_dir
from flask_openapi.utils.types import ordered_dict_to_dict
from flask_openapi.utils.version import is_openapi3
from flask_openapi.utils.views import has_valid_dispatch_view_docs, is_valid_method_view
from werkzeug.routing import Rule

try:
    from flask_mongorest import methods as fmr_methods
except ImportError:
    fmr_methods = None


def merge_specs(target: Dict, source: Dict):
    """
    Update target dictionary with values from the source, recursively.
    List items will be merged.

    :param target: target dictionary
    :type target: dict

    :param source: source dictionary
    :type source: dict

    :return: None
    """

    for key, value in source.items():
        if isinstance(value, dict):
            node: Any = target.setdefault(key, {})
            merge_specs(node, value)
        elif isinstance(value, list):
            node = target.setdefault(key, [])
            node.extend(value)
        else:
            target[key] = value


def get_specs(
    rules: Iterator[Rule],
    ignore_verbs: Set[str],
    optional_fields: List[str],
    sanitizer: Callable,
    openapi_version: Union[str, int],
    doc_dir: Optional[str] = None,
):
    """
    Extracts specs from rules

    :param rules: Flask url_map.iter_rules()
    :type rules: werkzeug.routing.Rule

    :param ignore_verbs: Verbs to ignore
    :type ignore_verbs: set

    :param optional_fields: Optional fields
    :type optional_fields: List[str]

    :param sanitizer: Sanitizer function
    :type sanitizer: Callable

    :param openapi_version: OpenAPI version
    :type openapi_version: str

    :param doc_dir: Directory containing docstrings
    :type doc_dir: str
    """
    specs: List = []

    for rule in rules:
        endpoint: Callable = current_app.view_functions[rule.endpoint]
        methods: Dict = {}
        is_mv: bool = is_valid_method_view(endpoint)

        if rule.methods:
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
                        endpoint_methods: Set = set(m.method for m in endpoint.methods)
                        if verb in endpoint_methods:
                            proxy_verb = rule.endpoint.replace(endpoint.__name__, "")
                            if proxy_verb:
                                methods[verb.lower()] = getattr(fmr_methods, proxy_verb)
                    else:
                        raise TypeError
                else:
                    methods[verb.lower()] = endpoint

        verbs: List = []

        for verb, method in methods.items():
            klass: Optional[Callable] = method.__dict__.get("view_class", None)
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

            swag: Dict = {}
            swag_def: Dict = {}

            swagged: bool = False

            if getattr(method, "specs_dict", None):
                definition: Dict = {}
                merge_specs(
                    swag, convert_schemas(deepcopy(method.specs_dict), definition)
                )
                swag_def = definition
                swagged = True

            view_class: Optional[Callable] = getattr(endpoint, "view_class", None)
            if view_class and issubclass(view_class, SwaggerView):  # type: ignore
                apispec_swag: Dict = {}

                # Don't need to alter definitions here
                # Since it only stays in apispec_attrs
                apispec_attrs: List[str] = optional_fields + [
                    "parameters",
                    "definitions",
                    "responses",
                    "summary",
                    "description",
                ]
                for attr in apispec_attrs:
                    value: str = getattr(view_class, attr)
                    if value:
                        apispec_swag[attr] = value
                # Don't need to change 'definitions' here
                # Since it would be appended later according to openapi
                apispec_definitions: Dict = apispec_swag.get("definitions", {})
                swag.update(convert_schemas(apispec_swag, apispec_definitions))
                swag_def = apispec_definitions

                swagged = True

            swag_path = None
            if doc_dir:
                swag_path = get_swag_path_from_doc_dir(
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


def get_schema_specs(schema_id, swagger):
    ignore_verbs = set(swagger.config.get("ignore_verbs", ("HEAD", "OPTIONS")))

    # technically only responses is non-optional
    optional_fields = swagger.config.get("optional_fields") or OPTIONAL_FIELDS

    openapi_version = swagger.config.get("openapi")

    with swagger.app.app_context():
        specs = get_specs(
            current_app.url_map.iter_rules(),
            ignore_verbs,
            optional_fields,
            swagger.sanitizer,
            openapi_version,
        )

        swags = (swag for _, verbs in specs for _, swag in verbs if swag is not None)

    for swag in swags:
        for d in swag.get("parameters", []):
            d_schema_id = d.get("schema", {}).get("id")
            if d_schema_id is not None and d_schema_id.lower() == schema_id.lower():
                return swag


def apispec_to_template(app, spec, definitions=None, paths=None):
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
    ret = ordered_dict_to_dict(spec_dict)
    return ret
