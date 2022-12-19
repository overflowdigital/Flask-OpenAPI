import codecs
import importlib
import inspect
import logging
import os
import re
from typing import Any


def get_swag_path_from_doc_dir(method: Any, view_class: Any, doc_dir: str, endpoint: Any):
    file_path = ''
    func = method.__func__ \
        if hasattr(method, '__func__') else method
    if view_class:
        file_path = os.path.join(
            doc_dir, endpoint.__name__, method.__name__ + '.yml')
    else:
        file_path = os.path.join(
            doc_dir, endpoint.__name__ + '.yml')
    if file_path and os.path.isfile(file_path):
        setattr(func, 'swag_type', 'yml')  # noqa
        setattr(func, 'swag_path', file_path)  # noqa
    else:
        # HACK: If the doc_dir doesn't quite match the filepath we take the doc_dir
        # and the current filepath without the /tmp
        file_path = getattr(func, 'swag_path', '')  # noqa
        if file_path and not os.path.isfile(file_path):
            regex = re.compile(r"(api.+)")
            try:
                file_path = doc_dir + regex.search(file_path)[0]
                if os.path.isfile(file_path):
                    setattr(func, 'swag_type', 'yml')  # noqa
                    setattr(func, 'swag_path', file_path)  # noqa
            except Exception:
                logging.exception(f"{file_path} is not a file")

    return file_path


def get_root_path(obj):
    """
    Get file path for object and returns its dirname
    """
    try:
        filename = os.path.abspath(obj.__globals__['__file__'])
    except (KeyError, AttributeError):
        if getattr(obj, '__wrapped__', None):
            # decorator package has been used in view
            return get_root_path(obj.__wrapped__)
        filename = inspect.getfile(obj)
    return os.path.dirname(filename)


def remove_suffix(fpath):  # pragma: no cover
    """Remove all file ending suffixes"""
    return os.path.splitext(fpath)[0]


def get_path_from_doc(full_doc):
    """
    If `file:` is provided import the file.
    """
    swag_path = full_doc.replace('file:', '').strip()
    swag_type = swag_path.split('.')[-1]
    return swag_path, swag_type


def load_from_file(swag_path, swag_type='yml', root_path=None):
    """
    Load specs from YAML file
    """
    if swag_type not in ('yaml', 'yml'):
        raise AttributeError("Currently only yaml or yml supported")
        # TODO: support JSON

    try:
        enc = detect_by_bom(swag_path)
        with codecs.open(swag_path, encoding=enc) as yaml_file:
            return yaml_file.read()
    except IOError:
        # not in the same dir, add dirname
        swag_path = os.path.join(
            root_path or os.path.dirname(__file__), swag_path
        )
        try:
            enc = detect_by_bom(swag_path)
            with codecs.open(swag_path, encoding=enc) as yaml_file:
                return yaml_file.read()
        except IOError:  # pragma: no cover
            swag_path = swag_path.replace("/", os.sep).replace("\\", os.sep)
            path = swag_path.replace(
                (root_path or os.path.dirname(__file__)), ''
            ).split(os.sep)[1:]
            package_spec = importlib.util.find_spec(path[0])
            if package_spec.has_location:
                # Improvement idea: Use package_spec.submodule_search_locations
                # if we're sure there's only going to be one search location.
                site_package = package_spec.origin.replace('/__init__.py', '')
            else:
                raise RuntimeError("Package does not have origin")
            swag_path = os.path.join(site_package, os.sep.join(path[1:]))
            with open(swag_path) as yaml_file:
                return yaml_file.read()
    except TypeError:
        logging.warning(f"File path {swag_path} is either doesnt exist or is in the wrong type")


def detect_by_bom(path, default='utf-8'):
    with open(path, 'rb') as f:
        raw = f.read(4)  # will read less if the file is smaller
    for enc, boms in \
            ('utf-8-sig', (codecs.BOM_UTF8,)),\
            ('utf-16', (codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)),\
            ('utf-32', (codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE)):
        if any(raw.startswith(bom) for bom in boms):
            return enc
    return default

def is_python_file(fpath):  # pragma: no cover
    """Naive Python module filterer"""
    return fpath.endswith(".py") and "__" not in fpath
