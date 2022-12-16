import logging
import re
from collections import defaultdict
from typing import Union

from flask import current_app

from flask_openapi.base import Swagger
from flask_openapi.constants import HTTP_METHODS, OAS3_SUB_COMPONENTS, OPTIONAL_FIELDS, OPTIONAL_OAS3_FIELDS
from flask_openapi.utils import extract_definitions, extract_schema, get_specs, get_vendor_extension_fields, is_openapi3, parse_definition_docstring

from werkzeug.routing import Rule


def get_definitions(data: dict, spec: dict) -> dict:
    definitions: dict = extract_schema(data)

    for name, def_model in current_app.swag.get_def_models(spec.get('definition_filter')).items():
        description, swag = parse_definition_docstring(def_model, current_app.swag.sanitizer)

        if name and swag:
            if description:
                swag.update({'description': description})
            definitions[name].update(swag)

    return definitions


def merge_sub_component(dest: dict, key: str, source: dict) -> dict:
    if len(source) > 0 and dest.get(key) is None:
        dest[key] = {}
    if len(source) > 0 and len(dest[key]) >= 0:
        dest[key].update(source)

    return dest


def get_operations(data: dict, spec: dict, rule: Rule, verb: str, optional_fields: list, path_verb: str = '') -> dict:
    swag: Swagger = current_app.swag

    definitions: dict = get_definitions(data, spec)

    openapi_version: str = swag.config.get('openapi')
    prefix_ids: list = swag.config.get('prefix_ids')
    params: list = swag.get('parameters', [])
    request_body: dict = swag.get('requestBody')
    callbacks: dict = swag.get("callbacks", {})
    responses: dict = swag.get('responses', {})

    defs: list = []
    operations: dict = {}
    operation: dict = {}

    if is_openapi3(openapi_version):
        source_components: dict = swag.get('components', {})
        update_schemas: Union[list, dict] = source_components.get('schemas', {})

        # clone list so we can modify
        # schemas are handled separately, so removethem here
        active_sub_components: list[str] = OAS3_SUB_COMPONENTS[:]
        active_sub_components.remove("schemas")

        for subcomponent in OAS3_SUB_COMPONENTS:
            data['components'] = merge_sub_component(data['components'], subcomponent, source_components.get(subcomponent, {}))
    else:
        update_schemas = swag.get('definitions', {})

    if type(update_schemas) == list and type(update_schemas[0]) == dict:
        update_schemas, = update_schemas

    definitions.update(update_schemas)

    if verb in swag.keys():
        verb_swag = swag.get(verb)
        if len(params) == 0 and verb.lower() in HTTP_METHODS:
            params = verb_swag.get('parameters', [])

    defs += extract_definitions(defs, endpoint=rule.endpoint, verb=verb, prefix_ids=prefix_ids, openapi_version=openapi_version)
    defs += extract_definitions(params, endpoint=rule.endpoint, verb=verb, prefix_ids=prefix_ids, openapi_version=openapi_version)

    if request_body:
        content = request_body.get("content", {})
        extract_definitions(list(content.values()), endpoint=rule.endpoint, verb=verb, prefix_ids=prefix_ids, openapi_version=openapi_version)

    if callbacks:
        callbacks = {str(key): value for key, value in callbacks.items()}
        extract_definitions(list(callbacks.values()), endpoint=rule.endpoint, verb=verb, prefix_ids=prefix_ids, openapi_version=openapi_version)

    if 'responses' in swag:
        responses = {str(key): value for key, value in responses.items()}

        if responses is not None:
            defs += extract_definitions(responses.values(), endpoint=rule.endpoint, verb=verb, prefix_ids=prefix_ids, openapi_version=openapi_version)

        for definition in defs:
            if 'id' not in definition:
                definitions.update(definition)
                continue
            def_id = definition.pop('id')
            if def_id is not None:
                definitions[def_id].update(definition)

    if swag.get('summary'):
        operation['summary'] = swag.get('summary')
    if swag.get('description'):
        operation['description'] = swag.get('description')
    if request_body:
        operation['requestBody'] = request_body
    if callbacks:
        operation['callbacks'] = callbacks
    if responses:
        operation['responses'] = responses
    if len(params) > 0:
        operation['parameters'] = params

    for key in optional_fields:
        if key in swag:
            value = swag.get(key)
            if key in ('produces', 'consumes'):
                if not isinstance(value, (list, tuple)):
                    value = [value]

            operation[key] = value

    if path_verb:
        operations[path_verb] = operation
    else:
        operations[verb] = operation

    return operations


def get_apispecs(endpoint: str = 'apispec_1') -> dict:
    swag: Swagger = current_app.swag
    spec: dict = {}
    openapi_version: str = swag.config.get('openapi')
    ignore_verbs: set[str] = set(swag.config.get('ignore_verbs', ("HEAD", "OPTIONS")))
    optional_fields: list = swag.config.get('optional_fields') or OPTIONAL_FIELDS
    operations: dict = {}
    specs: list = get_specs(
        swag.get_url_mappings(spec.get('rule_filter')),
        ignore_verbs,
        optional_fields,
        swag.sanitizer,
        openapi_version,
        doc_dir=swag.config.get('doc_dir')
    )

    if not current_app.debug and endpoint in swag.apispecs:
        return swag.apispecs[endpoint]

    for configured_spec in swag.config['specs']:
        if configured_spec['endpoint'] == endpoint:
            spec = configured_spec
            break

    if not spec:
        raise RuntimeError(f"Can't find specs by endpoint {endpoint}, check your config")

    data: dict = {
        "info": swag.config.get('info') or {
            "version": spec.get('version', swag.config.get('version', "0.0.1")),
            "title": spec.get('title', swag.config.get('title', "A swagger API")),
            "description": spec.get('description', swag.config.get('description', "")),
            "termsOfService": spec.get('termsOfService', swag.config.get('termsOfService', "/tos"))
        },
        "paths": swag.config.get('paths') or defaultdict(dict),
        "definitions": swag.config.get('definitions') or defaultdict(dict)
    }

    if openapi_version:
        data["openapi"] = openapi_version
    else:
        data["swagger"] = swag.config.get('swagger') or swag.config.get('swagger_version', "2.0")

    # If it's openapi3, #/components/schemas replaces #/definitions
    if is_openapi3(openapi_version):
        optional_oas3_fields: list = swag.config.get('optional_oas3_fields') or OPTIONAL_OAS3_FIELDS

        data.setdefault('components', {})['schemas'] = data['definitions']

        for key in optional_oas3_fields:
            if swag.config.get(key):
                data[key] = swag.config.get(key)

    # Support extension properties in the top level config
    top_level_extension_options = get_vendor_extension_fields(swag.config)

    if top_level_extension_options:
        data.update(top_level_extension_options)

    # if True schemaa ids will be prefized by function_method_{id}
    # for backwards compatibility with <= 0.5.14

    if swag.config.get('host'):
        data['host'] = swag.config.get('host')
    if swag.config.get("basePath"):
        data["basePath"] = swag.config.get('basePath')
    if swag.config.get('schemes'):
        data['schemes'] = swag.config.get('schemes')
    if swag.config.get("securityDefinitions"):
        data["securityDefinitions"] = swag.config.get('securityDefinitions')

    # set defaults from template
    if swag.template is not None:
        data.update(swag.template)

    for rule, verbs in specs:
        for verb, swag in verbs:
            if swag.get('paths'):
                try:
                    # /projects/{project_id}/alarms:
                    for path in swag.get('paths'):
                        # get:
                        for path_verb in swag.get('paths').get(path):
                            if path_verb == verb:
                                operations = get_operations(data, spec, rule, swag.get('paths').get(path).get(path_verb), optional_fields, path_verb)
                except AttributeError:
                    logging.exception(f'Swagger doc not in the correct format. {swag}')
            else:
                operations = get_operations(data, spec, rule, swag.get('paths').get(path).get(path_verb), optional_fields)

        if operations:
            srule: str = f"{swag.template.get('swaggerUiPrefix', '')}{rule}"
            base_path: str = swag.template.get('basePath', 'None')

            if base_path:
                if base_path.endswith('/'):
                    base_path = base_path[:-1]
                if base_path:
                    if srule.startswith(base_path):
                        srule = srule[len(base_path):]

            for arg in re.findall('(<([^<>]*:)?([^<>]*)>)', srule):
                srule = srule.replace(arg[0], '{%s}' % arg[2])

            for key, val in operations.items():
                if srule not in data['paths']:
                    data['paths'][srule] = {}
                if key in data['paths'][srule]:
                    data['paths'][srule][key].update(val)
                else:
                    data['paths'][srule][key] = val

    swag.apispecs[endpoint] = data

    if is_openapi3(openapi_version):
        del data['definitions']

    return data
