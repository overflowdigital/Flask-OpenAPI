import codecs
import importlib
import logging
import os
from typing import Literal, Optional


def detect_by_bom(path, default="utf-8"):
    with open(path, "rb") as f:
        raw = f.read(4)  # will read less if the file is smaller
    for enc, boms in (
        ("utf-8-sig", (codecs.BOM_UTF8,)),
        ("utf-16", (codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)),
        ("utf-32", (codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE)),
    ):
        if any(raw.startswith(bom) for bom in boms):
            return enc
    return default



    """
    Load specs from YAML file
    """
    if swag_type not in ("yaml", "yml"):
        raise AttributeError("Currently only yaml or yml supported")
        # TODO: support JSON

    try:
        enc = detect_by_bom(swag_path)
        with codecs.open(swag_path, encoding=enc) as yaml_file:
            return yaml_file.read()
    except IOError:
        # not in the same dir, add dirname
        swag_path = os.path.join(root_path or os.path.dirname(__file__), swag_path)
        try:
            enc = detect_by_bom(swag_path)
            with codecs.open(swag_path, encoding=enc) as yaml_file:
                return yaml_file.read()
        except IOError:  # pragma: no cover
            # if package dir
            # see https://github.com/rochacbruno/flasgger/pull/104
            # Still not able to reproduce this case
            # test are in examples/package_example
            # need more detail on how to reproduce IOError here
            swag_path = swag_path.replace("/", os.sep).replace("\\", os.sep)
            path = swag_path.replace(
                (root_path or os.path.dirname(__file__)), ""
            ).split(os.sep)[1:]
            package_spec = importlib.util.find_spec(path[0])
            if package_spec.has_location:
                # Improvement idea: Use package_spec.submodule_search_locations
                # if we're sure there's only going to be one search location.
                site_package = package_spec.origin.replace("/__init__.py", "")
            else:
                raise RuntimeError("Package does not have origin")
            swag_path = os.path.join(site_package, os.sep.join(path[1:]))
            with open(swag_path) as yaml_file:
                return yaml_file.read()
    except TypeError:
        logging.warning(
            f"File path {swag_path} is either doesnt exist or is in the wrong type"
        )
def load_from_file(path: str, file_type: Literal["yml", "yaml"] = "yml", root_path: Optional[str] = None) -> str:
    """
    Load swagger file from path

    :param path: path to swagger file
    :type path: str

    :param file_type: type of swagger file
    :type file_type: Literal['yml', 'yaml']

    :param root_path: root path to swagger file
    :type root_path: Optional[str]

    :return: Swagger file content
    :rtype: str
    """

    if file_type not in ("yaml", "yml"):
        raise AttributeError("Currently only yaml or yml supported")

    try:
        encoding: str = detect_by_bom(path)

        with codecs.open(path, encoding=encoding) as yaml_file:
            return yaml_file.read()

    except IOError:
        path = os.path.join(root_path or os.path.dirname(__file__), path)

        try:
            encoding = detect_by_bom(path)

            with codecs.open(path, encoding=encoding) as yaml_file:
                return yaml_file.read()

        except IOError:
            path = path.replace("/", os.sep).replace("\\", os.sep)
            path = path.replace((root_path or os.path.dirname(__file__)), "").split(os.sep)[1:]

            package_spec: Any = importlib.util.find_spec(path[0])

            if package_spec.has_location:
                site_package: str = package_spec.origin.replace("/__init__.py", "")
            else:
                raise RuntimeError("Package does not have origin")

            path = os.path.join(site_package, os.sep.join(path[1:]))

            with open(path) as yaml_file:
                return yaml_file.read()
    except TypeError:
        logging.warning(f"File path {path} either doesnt exist or is in the wrong type")