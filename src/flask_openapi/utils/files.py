import codecs
import importlib
import logging
import os
from typing import Any, Literal, Optional, List, Tuple


def detect_by_bom(path: str, default: str = "utf-8") -> str:
    """
    Detect encoding by BOM

    :param path: path to file
    :type path: str

    :param default: default encoding
    :type default: str

    :return: encoding
    :rtype: str
    """
    with open(path, "rb") as file:
        raw: bytes = file.read(4)

    encoding_map: Tuple = (
        ("utf-8-sig", (codecs.BOM_UTF8,)),
        ("utf-16", (codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)),
        ("utf-32", (codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE)),
    )

    for encodings, boms in encoding_map:
        if any(raw.startswith(bom) for bom in boms):
            return encodings

    return default


def load_from_file(
    path: str,
    file_type: Literal["yml", "yaml"] = "yml",
    root_path: Optional[str] = None,
) -> str:
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
            split_path: List[str] = path.replace(
                (root_path or os.path.dirname(__file__)), ""
            ).split(os.sep)[1:]

            package_spec: Any = importlib.util.find_spec(split_path[0])

            if package_spec.has_location:
                site_package: str = package_spec.origin.replace("/__init__.py", "")
            else:
                raise RuntimeError("Package does not have origin")

            path = os.path.join(site_package, os.sep.join(split_path[1:]))

            with open(path) as yaml_file:
                return yaml_file.read()
    except TypeError:
        logging.warning(f"File path {path} either doesnt exist or is in the wrong type")

    return ""
