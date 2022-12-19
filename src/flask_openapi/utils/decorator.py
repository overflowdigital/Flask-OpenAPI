import os
from functools import wraps

from flask_openapi.utils import get_root_path, validate

from six import string_types



def swag_from(
        specs=None, filetype=None, endpoint=None, methods=None,
        validation=False, schema_id=None, data=None, definition=None,
        validation_function=None, validation_error_handler=None):
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
        if not filepath.startswith('/'):
            if not hasattr(function, 'root_path'):
                function.root_path = get_root_path(function)
            res = os.path.join(function.root_path, filepath)
            return res
        return filepath

    def set_from_filepath(function):
        final_filepath = resolve_path(function, specs)
        function.swag_type = filetype or final_filepath.split('.')[-1]

        if endpoint or methods:
            if not hasattr(function, 'swag_paths'):
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
        """ Returns True if specs is a string or pathlib.Path
        """
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
            swag_path = getattr(function, 'swag_path', None)
            swag_paths = getattr(function, 'swag_paths', None)
            validate_args = {
                'filepath': swag_path or swag_paths,
                'root': getattr(function, 'root_path', None)
            }
        if isinstance(specs, dict):
            set_from_specs_dict(function)
            validate_args = {'specs': specs}

        @wraps(function)
        def wrapper(*args, **kwargs):
            if validation is True:
                validate(
                    data,
                    schema_id or definition,
                    validation_function=validation_function,
                    validation_error_handler=validation_error_handler,
                    **validate_args
                )
            return function(*args, **kwargs)
        return wrapper

    return decorator
