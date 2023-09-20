import inspect
import logging
import os
import re


def remove_suffix(fpath):  # pragma: no cover
    """Remove all file ending suffixes"""
    return os.path.splitext(fpath)[0]


def is_python_file(fpath):  # pragma: no cover
    """Naive Python module filterer"""
    return fpath.endswith(".py") and "__" not in fpath


def get_path_from_doc(full_doc):
    """
    If `file:` is provided import the file.
    """
    swag_path = full_doc.replace("file:", "").strip()
    swag_type = swag_path.split(".")[-1]
    return swag_path, swag_type


def get_root_path(obj):
    """
    Get file path for object and returns its dirname
    """
    try:
        filename = os.path.abspath(obj.__globals__["__file__"])
    except (KeyError, AttributeError):
        if getattr(obj, "__wrapped__", None):
            # decorator package has been used in view
            return get_root_path(obj.__wrapped__)
        filename = inspect.getfile(obj)
    return os.path.dirname(filename)


def get_swag_path_from_doc_dir(
    method: any, view_class: any, doc_dir: str, endpoint: any
):
    file_path = ""
    func = method.__func__ if hasattr(method, "__func__") else method
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
        file_path = getattr(func, "swag_path", None)
        if file_path and not os.path.isfile(file_path):
            regex = re.compile(r"(api.+)")
            try:
                file_path = doc_dir + regex.search(file_path)[0]
                if os.path.isfile(file_path):
                    setattr(func, "swag_type", "yml")
                    setattr(func, "swag_path", file_path)
            except Exception:
                logging.exception(f"{file_path} is not a file")

    return file_path
