import os
from functools import wraps

from flask import request
from six import string_types

from flask_openapi.core.marshmallow_apispec import Schema
from flask_openapi.core.validation import validate
from flask_openapi.utils.constants import DEFAULT_FIELDS
from flask_openapi.utils.paths import get_root_path


def swag_from(
    specs=None,
    filetype=None,
    endpoint=None,
    methods=None,
    validation=False,
    schema_id=None,
    data=None,
    definition=None,
    validation_function=None,
    validation_error_handler=None,
):
    """
    Takes a filename.yml, a dictionary or object and loads swagger specs.

    :param specs: a filepath, a dictionary or an object
    :param filetype: yml or yaml (json and py to be implemented)
    :param endpoint: endpoint to build definition name
    :param methods: method to build method based specs
    :param validation: perform validation?
    :param schema_id: Definition id ot name to use for validation
    :param data: data to validate (default is request.json)
    :param definition: alias to schema_id
    :param validation_function:
        custom validation function which takes the positional
        arguments: data to be validated at first and schema to validate
        against at second
    :param validation_error_handler: custom function to handle
        exceptions thrown when validating which takes the exception
        thrown as the first, the data being validated as the second and
        the schema being used to validate as the third argument
    """

    def resolve_path(function, filepath):
        try:
            from pathlib import Path

            if isinstance(filepath, Path):
                filepath = str(filepath)
        except ImportError:
            pass
        if not filepath.startswith("/"):
            if not hasattr(function, "root_path"):
                function.root_path = get_root_path(function)
            res = os.path.join(function.root_path, filepath)
            return res
        return filepath

    def set_from_filepath(function):
        final_filepath = resolve_path(function, specs)
        function.swag_type = filetype or final_filepath.split(".")[-1]

        if endpoint or methods:
            if not hasattr(function, "swag_paths"):
                function.swag_paths = {}

        if not endpoint and not methods:
            function.swag_path = final_filepath
        elif endpoint and methods:
            for verb in methods:
                key = "{}_{}".format(endpoint, verb.lower())
                function.swag_paths[key] = final_filepath
        elif endpoint and not methods:
            function.swag_paths[endpoint] = final_filepath
        elif methods and not endpoint:
            for verb in methods:
                function.swag_paths[verb.lower()] = final_filepath

    def set_from_specs_dict(function):
        function.specs_dict = specs

    def is_path(specs):
        """Returns True if specs is a string or pathlib.Path"""
        is_str_path = isinstance(specs, string_types)
        try:
            from pathlib import Path

            is_py3_path = isinstance(specs, Path)
            return is_str_path or is_py3_path
        except ImportError:
            return is_str_path

    def decorator(function):
        if is_path(specs):
            set_from_filepath(function)
            # function must have or a single swag_path or a list of them
            swag_path = getattr(function, "swag_path", None)
            swag_paths = getattr(function, "swag_paths", None)
            validate_args = {
                "filepath": swag_path or swag_paths,
                "root": getattr(function, "root_path", None),
            }
        if isinstance(specs, dict):
            set_from_specs_dict(function)
            validate_args = {"specs": specs}

        @wraps(function)
        def wrapper(*args, **kwargs):
            if validation is True:
                validate(
                    data,
                    schema_id or definition,
                    validation_function=validation_function,
                    validation_error_handler=validation_error_handler,
                    **validate_args,
                )
            return function(*args, **kwargs)

        return wrapper

    return decorator


def validate_annotation(an, var):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if an.swag_validate:
                payload = None

                if an.swag_in == "query":
                    payload = dict(request.args)

                elif an.swag_in == "body" and request.is_json:
                    payload = request.json

                validate(
                    payload,
                    specs=an.to_specs_dict(),
                    validation_function=an.swag_validation_function,
                    validation_error_handler=an.swag_validation_error_handler,
                    require_data=an.swag_require_data
                    # handle openapiversion later
                )

            return f(*args, **kwargs, **{var: payload})

        return wrapper

    return decorator


def swag_annotation(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not kwargs.pop("swag", False):
            return f(*args, **kwargs)

        function = args[2]

        specs = {}
        for key, value in DEFAULT_FIELDS.items():
            specs[key] = kwargs.pop(key, value)

        for variable, annotation in function.__annotations__.items():
            if issubclass(annotation, Schema):
                annotation = annotation()
                data = annotation.to_specs_dict()

                for row in data["parameters"]:
                    specs["parameters"].append(row)
                specs["definitions"].update(data["definitions"])

                function = validate_annotation(annotation, variable)(function)

            elif issubclass(annotation, int):
                m = {
                    "name": variable,
                    "in": "path",
                    "type": "integer",
                    "required": True,
                }
                if ("int(signed=True):" + variable) in args[0]:
                    m["minimum"] = 0
                specs["parameters"].append(m)

            elif issubclass(annotation, str):
                specs["parameters"].append(
                    {"name": variable, "in": "path", "type": "string", "required": True}
                )

        function.specs_dict = specs
        args = list(args)
        args[2] = function
        args = tuple(args)

        return f(*args, **kwargs)

    return wrapper
