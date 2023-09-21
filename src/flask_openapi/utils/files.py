import codecs
import importlib
import logging
import os


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


def load_from_file(swag_path, swag_type="yml", root_path=None):
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
