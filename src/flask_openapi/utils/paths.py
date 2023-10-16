import inspect
import logging
import os
import re
from typing import Any, Tuple, cast, Literal


def remove_suffix(path: str) -> str:
    """
    Remove suffix from path

    :param path: path to file
    :type path: str

    :return: path without suffix
    :rtype: str
    """

    return os.path.splitext(path)[0]


def is_python_file(path: str) -> bool:
    """
    Check if path is python file

    :param path: path to file
    :type path: str

    :return: True if path is python file
    :rtype: bool
    """

    return path.endswith(".py") and "__" not in path


def get_path_from_doc(full_doc: str) -> Tuple[str, Literal["yml", "yaml"]]:
    """
    Get path and type from doc

    :param full_doc: full doc
    :type full_doc: str

    :return: path and type
    :rtype: tuple[str, str]
    """

    swag_path: str = full_doc.replace("file:", "").strip()
    swag_type: Literal["yml", "yaml"] = cast(
        Literal["yml", "yaml"], swag_path.split(".")[-1]
    )

    return swag_path, swag_type


def get_root_path(obj: Any) -> str:
    """
    Get file path for object and returns its dirname

    :param obj: object
    :type obj: Any

    :return: root path
    :rtype: str
    """

    try:
        filename: str = os.path.abspath(obj.__globals__["__file__"])
    except (KeyError, AttributeError):
        if getattr(obj, "__wrapped__", None):
            return get_root_path(obj.__wrapped__)

        filename = inspect.getfile(obj)

    return os.path.dirname(filename)


def get_swag_path_from_doc_dir(
    method: Any, view_class: Any, doc_dir: str, endpoint: Any
) -> str:
    """
    Get swagger path from doc dir

    :param method: method
    :type method: Any

    :param view_class: view class
    :type view_class: Any

    :param doc_dir: doc dir
    :type doc_dir: str

    :param endpoint: endpoint
    :type endpoint: Any

    :return: swagger path
    :rtype: str
    """

    file_path: str = ""
    func: Any = method.__func__ if hasattr(method, "__func__") else method

    if view_class:
        file_path = os.path.join(doc_dir, endpoint.__name__, method.__name__ + ".yml")
    else:
        file_path = os.path.join(doc_dir, endpoint.__name__ + ".yml")

    if file_path and os.path.isfile(file_path):
        setattr(func, "swag_type", "yml")
        setattr(func, "swag_path", file_path)
    else:
        # HACK: If the doc_dir doesn't quite match the filepath we take the doc_dir
        # and the current filepath without the /tmp
        file_path = getattr(func, "swag_path", "")

        if file_path and not os.path.isfile(file_path):
            regex = re.compile(r"(api.+)")

            try:
                matches = regex.search(file_path)

                if matches:
                    file_path = doc_dir + matches.group(0)

                if os.path.isfile(file_path):
                    setattr(func, "swag_type", "yml")
                    setattr(func, "swag_path", file_path)
            except Exception:
                logging.exception(f"{file_path} is not a file")

    return file_path
