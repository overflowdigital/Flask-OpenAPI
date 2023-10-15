import inspect
import os
import re
from collections import defaultdict
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple, Union

import yaml
from flask import request
from flask_openapi.utils.files import load_from_file
from flask_openapi.utils.paths import get_path_from_doc, get_root_path
from flask_openapi.utils.version import is_openapi3


def parse_imports(doc_string: str, root_path: Optional[str] = None):
    """
    Supports `import: otherfile.yml` in docstring specs

    :param full_doc: docstring
    :type full_doc: str

    :param root_path: root path to swagger file
    :type root_path: Optional[str]

    :return: Swagger file content
    :rtype: str
    """
    regex: re.Pattern[str] = re.compile('import: "(.*)"')
    import_prop: Optional[re.Match[str]] = regex.search(doc_string)

    if import_prop:
        start: int = import_prop.start()
        spaces_num: int = start - doc_string.rfind("\n", 0, start) - 1
        filepath: str = import_prop.group(1)

        if filepath.startswith("/"):
            imported_doc: str = load_from_file(filepath)
        else:
            imported_doc = load_from_file(filepath, root_path=root_path)

        indented_imported_doc: str = imported_doc.replace("\n", "\n" + " " * spaces_num)
        doc_string = regex.sub(indented_imported_doc, doc_string, count=1)

        return parse_imports(doc_string)

    return doc_string


def parse_docstring(
    obj: Any,
    process_doc: Callable,
    endpoint: Optional[str] = None,
    verb: Optional[str] = None,
    swag_path: Optional[str] = None,
) -> Tuple[str, str, Dict]:
    """
    Gets swag data for method/view docstring

    :param obj: method/view
    :type obj: Any

    :param process_doc: function to process docstring
    :type process_doc: Callable

    :param endpoint: endpoint name
    :type endpoint: Optional[str]

    :param verb: http verb
    :type verb: Optional[str]

    :param swag_path: path to swagger file
    :type swag_path: Optional[str]

    :return: first line, other lines, swag
    :rtype: Tuple[str, str, dict]
    """

    first_line: str = ""
    other_lines: str = ""
    swag: Dict = {}
    full_doc: str = ""

    if not swag_path:
        swag_path = getattr(obj, "swag_path", None)

    swag_type: Literal["yml", "yaml"] = getattr(obj, "swag_type", "yml")
    swag_paths: List[str] = getattr(obj, "swag_paths", [])
    root_path: str = get_root_path(obj)
    from_file: bool = False

    if swag_path:
        full_doc = load_from_file(swag_path, swag_type)
        from_file = True
    elif swag_paths and verb:
        for key in (f"{endpoint}_{verb}", endpoint, verb.lower()):
            if key and key in swag_paths:
                path: str = swag_paths[key]  # type: ignore  # this is a str i promise...
                full_doc = load_from_file(path, swag_type)
                break
        from_file = True
    else:
        full_doc = inspect.getdoc(obj) or ""

    if full_doc:
        if full_doc.startswith("file:"):
            if not hasattr(obj, "root_path"):
                obj.root_path = root_path
            swag_path, swag_type = get_path_from_doc(full_doc)
            doc_filepath = os.path.join(obj.root_path, swag_path)
            full_doc = load_from_file(doc_filepath, swag_type)
            from_file = True

        full_doc = parse_imports(full_doc, root_path)

        yaml_sep: int = full_doc.find("---")

        if yaml_sep != -1:
            line_feed: int = full_doc.find("\n")
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


def parse_definition_docstring(obj: Any, process_doc: Callable) -> Tuple[str, Dict]:
    """
    Gets swag data from docstring for class based definitions

    :param obj: class
    :type obj: Any

    :param process_doc: function to process docstring
    :type process_doc: Callable

    :param doc_dir: doc dir
    :type doc_dir: Optional[str]

    :return: doc_lines, swag
    :rtype: Tuple[str, dict]
    """
    doc_lines: str = ""
    swag: Dict = {}
    full_doc: str = ""
    swag_path: str = getattr(obj, "swag_path", "")
    swag_type: Literal["yml", "yaml"] = getattr(obj, "swag_type", "yml")

    if swag_path:
        full_doc = load_from_file(swag_path, swag_type)
    else:
        full_doc = inspect.getdoc(obj) or ""

    if full_doc:
        if full_doc.startswith("file:"):
            if not hasattr(obj, "root_path"):
                obj.root_path = get_root_path(obj)
            swag_path, swag_type = get_path_from_doc(full_doc)
            doc_filepath: str = os.path.join(obj.root_path, swag_path)
            full_doc = load_from_file(doc_filepath, swag_type)

        yaml_sep: int = full_doc.find("---")
        if yaml_sep != -1:
            doc_lines = process_doc(full_doc[: yaml_sep - 1]) if yaml_sep else None
            swag = yaml.safe_load(full_doc[yaml_sep:])
        else:
            doc_lines = process_doc(full_doc)

    return doc_lines, swag


def parse_definitions(
    alist: List[Dict],
    level: int = 0,
    endpoint: Optional[str] = None,
    verb: Optional[str] = None,
    prefix_ids: bool = False,
    openapi_version: Optional[Union[str, int]] = None,
) -> List[Dict]:
    """
    Since we couldn't be bothered to register models elsewhere
    our definitions need to be extracted from the parameters.
    We require an 'id' field for the schema to be correctly
    added to the definitions list.

    :param alist: list of parameters
    :type alist: List[dict]

    :param level: level of recursion
    :type level: int

    :param endpoint: endpoint name
    :type endpoint: Optional[str]

    :param verb: http verb
    :type verb: Optional[str]

    :param prefix_ids: prefix ids with endpoint_verb
    :type prefix_ids: bool

    :param openapi_version: openapi version
    :type openapi_version: Optional[str]

    :return: list of definitions
    :rtype: List[dict]
    """

    endpoint = endpoint or request.endpoint.lower()  # type: ignore
    verb = verb or request.method.lower() or ""  # type: ignore
    endpoint = endpoint.replace(".", "_")

    def _extract_array_defs(source: Dict) -> List[Dict]:
        """
        Extracts definitions identified by `id`
        """
        ret: List[Dict] = []
        items: Optional[Dict] = source.get("items")

        if items and "schema" in items:
            ret += parse_definitions(
                [items], level + 1, endpoint, verb, prefix_ids, openapi_version
            )
        return ret

    defs: List[Dict] = []

    for item in alist:
        if not getattr(item, "get"):
            raise RuntimeError("definitions must be a list of dicts")

        schema: Optional[Dict] = item.get("schema")

        if schema:
            schema_id: Optional[str] = schema.get("id")

            if schema_id:
                if prefix_ids:
                    schema["id"] = schema_id = f"{endpoint}_{verb}_{schema_id}"

                defs.append(schema)
                ref_path: str = ""

                if is_openapi3(openapi_version):
                    ref_path = "#/components/schemas/"
                else:
                    ref_path = "#/definitions/"

                ref: Dict[str, str] = {"$ref": f"{ref_path}{schema_id}"}

                if level == 0:
                    item["schema"] = ref
                else:
                    item.update(ref)
                    del item["schema"]

            properties: Any = schema.get("properties")

            if properties:
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


def parse_schema(spec: Dict) -> Dict:
    """
    Returns schema resources according to openapi version

    :param spec: swagger spec
    :type spec: dict

    :return: schema resources
    :rtype: dict
    """
    openapi_version: Optional[Union[str, int]] = spec.get("openapi", None)

    if is_openapi3(openapi_version):
        return spec.get("components", {}).get("schemas", defaultdict(dict))
    else:
        return spec.get("definitions", defaultdict(dict))


def convert_references_to_openapi3(obj: Any) -> None:
    """
    Convert references to openapi3 format

    :param obj: object
    :type obj: Any

    :return: None
    :rtype: None
    """
    for key, val in obj.items():
        if key == "$ref":
            obj[key] = val.replace("definitions", "components/schemas")

        if isinstance(val, dict):
            convert_references_to_openapi3(val)


def convert_response_definitions_to_openapi3(
    response: Dict, media_types: List[str]
) -> None:
    """
    Convert response definitions to openapi3 format

    :param response: response
    :type response: dict

    :param media_types: media types
    :type media_types: List[str]

    :return: None
    """
    if "schema" in response:
        convert_references_to_openapi3(response["schema"])
        if "content" not in response:
            response["content"] = {}
            for media_type in media_types:
                response["content"][media_type] = {"schema": dict(response["schema"])}
        del response["schema"]


def convert_responses_to_openapi3(responses: Dict, media_types: List[str]) -> None:
    """
    Convert responses to openapi3 format

    :param responses: responses
    :type responses: dict

    :param media_types: media types
    :type media_types: List[str]

    :return: None
    """
    for val in responses.values():
        convert_response_definitions_to_openapi3(val, media_types)
