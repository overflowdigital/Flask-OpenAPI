import inspect
import os
import re
from collections import defaultdict

import yaml
from flask import request

from flask_openapi.utils.files import load_from_file
from flask_openapi.utils.paths import get_path_from_doc, get_root_path
from flask_openapi.utils.version import is_openapi3


def parse_imports(full_doc, root_path=None):
    """
    Supports `import: otherfile.yml` in docstring specs
    """
    regex = re.compile('import: "(.*)"')
    import_prop = regex.search(full_doc)
    if import_prop:
        start = import_prop.start()
        spaces_num = start - full_doc.rfind("\n", 0, start) - 1
        filepath = import_prop.group(1)
        if filepath.startswith("/"):
            imported_doc = load_from_file(filepath)
        else:
            imported_doc = load_from_file(filepath, root_path=root_path)
        indented_imported_doc = imported_doc.replace("\n", "\n" + " " * spaces_num)
        full_doc = regex.sub(indented_imported_doc, full_doc, count=1)
        return parse_imports(full_doc)
    return full_doc


def parse_docstring(obj, process_doc, endpoint=None, verb=None, swag_path=None):
    """
    Gets swag data for method/view docstring
    """
    first_line, other_lines, swag = None, None, None

    full_doc = None
    if not swag_path:
        swag_path = getattr(obj, "swag_path", None)
    swag_type = getattr(obj, "swag_type", "yml")
    swag_paths = getattr(obj, "swag_paths", None)
    root_path = get_root_path(obj)
    from_file = False

    if swag_path is not None:
        full_doc = load_from_file(swag_path, swag_type)
        from_file = True
    elif swag_paths is not None:
        for key in ("{}_{}".format(endpoint, verb), endpoint, verb.lower()):
            if key in swag_paths:
                full_doc = load_from_file(swag_paths[key], swag_type)
                break
        from_file = True
        # TODO: handle multiple root_paths
        # to support `import: ` from multiple places
    else:
        full_doc = inspect.getdoc(obj)

    if full_doc:
        if full_doc.startswith("file:"):
            if not hasattr(obj, "root_path"):
                obj.root_path = root_path
            swag_path, swag_type = get_path_from_doc(full_doc)
            doc_filepath = os.path.join(obj.root_path, swag_path)
            full_doc = load_from_file(doc_filepath, swag_type)
            from_file = True

        full_doc = parse_imports(full_doc, root_path)

        yaml_sep = full_doc.find("---")

        if yaml_sep != -1:
            line_feed = full_doc.find("\n")
            if line_feed != -1:
                first_line = process_doc(full_doc[:line_feed])
                other_lines = process_doc(full_doc[line_feed + 1 : yaml_sep])
                swag = yaml.safe_load(full_doc[yaml_sep + 4 :])
        else:
            if from_file:
                swag = yaml.safe_load(full_doc)
            else:
                first_line = full_doc

    return first_line, other_lines, swag


def parse_definition_docstring(obj, process_doc, doc_dir=None):
    """
    Gets swag data from docstring for class based definitions
    """
    doc_lines, swag = None, None

    full_doc = None
    swag_path = getattr(obj, "swag_path", None)
    swag_type = getattr(obj, "swag_type", "yml")

    if swag_path is not None:
        full_doc = load_from_file(swag_path, swag_type)
    else:
        full_doc = inspect.getdoc(obj)

    if full_doc:
        if full_doc.startswith("file:"):
            if not hasattr(obj, "root_path"):
                obj.root_path = get_root_path(obj)
            swag_path, swag_type = get_path_from_doc(full_doc)
            doc_filepath = os.path.join(obj.root_path, swag_path)
            full_doc = load_from_file(doc_filepath, swag_type)

        yaml_sep = full_doc.find("---")
        if yaml_sep != -1:
            doc_lines = process_doc(full_doc[: yaml_sep - 1]) if yaml_sep else None
            swag = yaml.safe_load(full_doc[yaml_sep:])
        else:
            doc_lines = process_doc(full_doc)

    return doc_lines, swag


def parse_definitions(
    alist, level=None, endpoint=None, verb=None, prefix_ids=False, openapi_version=None
):
    """
    Since we couldn't be bothered to register models elsewhere
    our definitions need to be extracted from the parameters.
    We require an 'id' field for the schema to be correctly
    added to the definitions list.
    """
    endpoint = endpoint or request.endpoint.lower()
    verb = verb or request.method.lower()
    endpoint = endpoint.replace(".", "_")

    def _extract_array_defs(source):
        """
        Extracts definitions identified by `id`
        """
        # extract any definitions that are within arrays
        # this occurs recursively
        ret = []
        items = source.get("items")
        if items is not None and "schema" in items:
            ret += parse_definitions(
                [items], level + 1, endpoint, verb, prefix_ids, openapi_version
            )
        return ret

    # for tracking level of recursion
    if level is None:
        level = 0

    defs = list()
    for item in alist:
        if not getattr(item, "get"):
            raise RuntimeError("definitions must be a list of dicts")
        schema = item.get("schema")
        if schema is not None:
            schema_id = schema.get("id")
            if schema_id is not None:
                # add endpoint_verb to schema id to avoid conflicts
                if prefix_ids:
                    schema["id"] = schema_id = "{}_{}_{}".format(
                        endpoint, verb, schema_id
                    )
                # ^ api['SWAGGER']['prefix_ids'] = True
                # ... for backwards compatibility with <= 0.5.14

                defs.append(schema)

                ref_path = None
                if is_openapi3(openapi_version):
                    ref_path = "#/components/schemas/"
                else:
                    ref_path = "#/definitions/"
                ref = {"$ref": "{}{}".format(ref_path, schema_id)}

                # only add the reference as a schema if we are in a
                # response or a parameter i.e. at the top level
                # directly ref if a definition is used within another
                # definition
                if level == 0:
                    item["schema"] = ref
                else:
                    item.update(ref)
                    del item["schema"]

            # extract any definitions that are within properties
            # this occurs recursively
            properties = schema.get("properties")
            if properties is not None:
                defs += parse_definitions(
                    properties.values(),
                    level + 1,
                    endpoint,
                    verb,
                    prefix_ids,
                    openapi_version,
                )

            defs += _extract_array_defs(schema)

        defs += _extract_array_defs(item)

    return defs


def parse_schema(spec: dict) -> defaultdict:
    """
    Returns schema resources according to openapi version
    """
    openapi_version = spec.get("openapi", None)
    if is_openapi3(openapi_version):
        return spec.get("components", {}).get("schemas", defaultdict(dict))
    else:  # openapi2
        return spec.get("definitions", defaultdict(dict))


def convert_references_to_openapi3(obj):
    for key, val in obj.items():
        if key == "$ref":
            obj[key] = val.replace("definitions", "components/schemas")

        if isinstance(val, dict):
            convert_references_to_openapi3(val)


def convert_response_definitions_to_openapi3(response, media_types):
    if "schema" in response:
        convert_references_to_openapi3(response["schema"])
        if "content" not in response:
            response["content"] = {}
            for media_type in media_types:
                response["content"][media_type] = {"schema": dict(response["schema"])}
        del response["schema"]


def convert_responses_to_openapi3(responses, media_types):
    for val in responses.values():
        convert_response_definitions_to_openapi3(val, media_types)
