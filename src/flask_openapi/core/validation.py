import copy
import inspect
import os
import sys
from typing import Any, Callable, Optional, Union, Dict, List

import jsonschema
import yaml
from flask import abort, request, Response
from flask_openapi.core.parser import parse_definitions, parse_schema
from flask_openapi.utils.files import load_from_file


def __replace_ref(schema: Dict, relative_path: str, swag: Dict) -> Dict:
    """
    Replace $ref in schema

    :param schema: schema
    :type schema: dict

    :param relative_path: relative path
    :type relative_path: str

    :param swag: swagger
    :type swag: dict

    :return: new value
    :rtype: dict
    """
    absolute_path: str = os.path.dirname(sys.argv[0])
    new_value: Dict = {}

    for key, value in schema.items():
        if isinstance(value, dict):
            new_value[key] = __replace_ref(value, relative_path, swag)
        elif key == "$ref":
            if len(value) > 2 and value.startswith("#/"):  # $ref is local
                content: Dict = swag
                for id in value.split("/")[1:]:
                    content = content[id]
                return (
                    __replace_ref(content, relative_path, swag)
                    if isinstance(content, dict)
                    else content
                )

            if len(value) > 0 and value[0] == "/":
                file_ref_path: str = absolute_path + value
            else:
                file_ref_path = relative_path + "/" + value

            relative_path = os.path.dirname(file_ref_path)

            with open(file_ref_path) as file:
                file_content: str = file.read()
                comment_index: int = file_content.rfind("---")

                if comment_index > 0:
                    comment_index = comment_index + 3
                else:
                    comment_index = 0

                content = yaml.safe_load((file_content[comment_index:]))
                new_value = content

                if isinstance(content, dict):
                    new_value = __replace_ref(content, relative_path, swag)
        else:
            new_value[key] = value

    return new_value


def validate(
    data: Optional[Any] = None,
    schema_id: Optional[str] = None,
    filepath: Optional[str] = None,
    root: Optional[str] = None,
    definition: Optional[str] = None,
    specs: Optional[Dict] = None,
    validation_function: Optional[Callable] = None,
    validation_error_handler: Optional[Callable] = None,
    require_data: bool = True,
    openapi_version: Optional[Union[str, int]] = None,
) -> None:
    """
    This method is available to use YAML swagger definitions file
    or specs (dict or object) to validate data against its jsonschema.

    example:
        validate({"item": 1}, 'item_schema', 'defs.yml', root=__file__)
        validate(request.json, 'User', specs={'definitions': {'User': ...}})

    :param data: data to validate, by default is request.json
    :type data: Optional[Any]

    :param schema_id: The definition id to use to validate (from specs)
    :type schema_id: Optional[str]

    :param filepath: definition filepath to load specs
    :type filepath: Optional[str]

    :param root: root folder (inferred if not provided), unused if path
        starts with `/`
    :type root: Optional[str]

    :param definition: Alias to schema_id (kept for backwards
        compatibility)
    :type definition: Optional[str]

    :param specs: load definitions from dict or object passed here
        instead of a file.
    :type specs: Optional[dict]

    :param validation_function: custom validation function which takes
        the positional arguments: data to be validated at first and
        schema to validate against at second
    :type validation_function: Optional[Callable]

    :param validation_error_handler: custom function to handle
        exceptions thrown when validating which takes the exception
        thrown as the first, the data being validated as the second and
        the schema being used to validate as the third argument
    :type validation_error_handler: Optional[Callable]

    :param require_data: is the data param required?
    :type require_data: bool

    :param openapi_version: openapi version to use
    :type openapi_version: Optional[str]

    :return: None
    """
    schema_id = schema_id or definition

    # for backwards compatibility with function signature
    if filepath is None and specs is None:
        abort(Response("Filepath or specs is needed to validate", status=500))

    if data is None:
        data = request.json  # defaults
    elif callable(data):
        data = data()

    if not data and require_data:
        abort(Response("No data to validate", status=400))

    # not used anymore but kept to reuse with marshmallow
    endpoint: str = (request.endpoint or "").lower().replace(".", "_")
    verb: str = request.method.lower()

    if filepath:
        if not root:
            try:
                frame_info: inspect.FrameInfo = inspect.stack()[1]
                root = os.path.dirname(os.path.abspath(frame_info[1]))
            except Exception:
                root = None
        else:
            root = os.path.dirname(root)

        if not filepath.startswith("/"):
            final_filepath: str = os.path.join(root, filepath)  # type: ignore
        else:
            final_filepath = filepath

        full_doc: str = load_from_file(final_filepath)
        yaml_start: int = full_doc.find("---")
        swag: Dict = yaml.safe_load(full_doc[yaml_start if yaml_start >= 0 else 0 :])
    else:
        swag = copy.deepcopy(specs or {})

    params: List = [item for item in swag.get("parameters", []) if item.get("schema")]
    definitions: Dict = {}
    main_def: Dict = {}
    raw_definitions: List[dict] = parse_definitions(
        params, endpoint=endpoint, verb=verb, openapi_version=openapi_version
    )

    if schema_id is None:
        for param in params:
            if param.get("in") == "body":
                schema_id = param.get("schema", {}).get("$ref")
                if schema_id:
                    schema_id = schema_id.split("/")[-1]
                    break  # consider only the first

    if schema_id is None:
        # if it is still none use first raw_definition extracted
        if raw_definitions:
            schema_id = raw_definitions[0].get("id")

    for defi in raw_definitions:
        if defi["id"].lower() == schema_id.lower():  # type: ignore
            main_def = defi.copy()
        else:
            definitions[defi["id"]] = defi

    # support definitions informed in dict
    if schema_id in parse_schema(swag):
        main_def = parse_schema(swag).get(schema_id)  # type: ignore

    # Doensn't need to alter 'definitions' according to open api
    # Since it main_def exists only in this function
    main_def["definitions"] = definitions

    for _, value in definitions.items():
        if "id" in value:
            del value["id"]

    if validation_function is None:
        validation_function = jsonschema.validate

    absolute_path: str = os.path.dirname(sys.argv[0])

    if filepath is None:
        relative_path = absolute_path
    else:
        relative_path = os.path.dirname(filepath)

    main_def = __replace_ref(main_def, relative_path, swag)

    try:
        validation_function(data, main_def)
    except Exception as err:
        if validation_error_handler is not None:
            validation_error_handler(err, data, main_def)
        else:
            abort(Response("Fatal error", status=400))
