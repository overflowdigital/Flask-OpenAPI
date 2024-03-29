import json
import os
import random
from importlib import import_module

import pytest
from flask import Flask

from flask_openapi import Swagger
from flask_openapi.utils.paths import is_python_file, remove_suffix

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
TEST_SUITE = os.path.join(REPO_ROOT, "ci/tests/suite")


def get_specs_data(mod):
    """
    return all specs dictionary for some app
    """
    # for each example app in /examples folder
    client = mod.app.test_client()
    # init swag if not yet inititalized (no-routes example)
    specs_route = None
    specs_data = {}
    if getattr(mod.app, "swag", None) is None:
        _swag = Swagger()
        _swag.config["endpoint"] = str(random.randint(1, 5000))
        _swag.init_app(mod.app)
    # get all the specs defined for the example app
    else:
        try:
            ui_config = mod.swag.config

            if ui_config.get("swagger_ui") is False:
                return specs_data

            specs_route = ui_config.get("specs_route", "/apidocs/")
        except AttributeError:
            pass

    if specs_route is None:
        specs_route = "/apidocs/"

    apidocs = client.get("?".join((specs_route, "json=true")))
    specs = json.loads(apidocs.data.decode("utf-8")).get("specs")

    for spec in specs:
        # for each spec get the spec url
        url = spec["url"]
        response = client.get(url)
        decoded = response.data.decode("utf-8")
        print(mod)
        specs_data[url] = json.loads(decoded)

    return specs_data


def pathify(basenames, examples_dir=TEST_SUITE):  # pragma: no cover
    """*nix to python module path"""
    example = examples_dir.replace("/", ".")
    return [example + basename for basename in basenames]


def get_examples(examples_dir=TEST_SUITE):  # pragma: no cover
    """All example modules"""
    all_files = os.listdir(examples_dir)
    python_files = [f for f in all_files if is_python_file(f)]
    basenames = [remove_suffix(f) for f in python_files]
    modules = [import_module(f"suite.{module}") for module in basenames]
    return [module for module in modules if getattr(module, "app", None) is not None]


def get_test_metadata(mod):
    """Create a dictionary of test metadata defined in an example

    Every top-level constant prefixed with "_TEST_META_" is treated as
    metadata which may control test behavior. The prefix is stripped and the
    remaining text is lowercased to form the key in the metadata dictionary.

    Example: '_TEST_META_SKIP_FULL_VALIDATION' -> 'skip_full_validation'
    """

    test_metadata_prefix = "_TEST_META_"
    return {
        key[len(test_metadata_prefix) :].lower(): getattr(mod, key)
        for key in mod.__dict__
        if key.startswith(test_metadata_prefix)
    }


def pytest_generate_tests(metafunc):
    """
    parametrize tests using examples() function
    to generate one test for each examples/
    """

    if "test_data" in metafunc.fixturenames:
        test_data = [
            (mod, mod.app.test_client(), get_specs_data(mod), get_test_metadata(mod))
            for mod in get_examples()
        ]

        metafunc.parametrize("test_data", test_data, ids=lambda x: x[0].__name__)


@pytest.fixture(scope="function")
def app():
    yield Flask(__name__)


@pytest.fixture(scope="function")
def cli_runner(app):
    yield app.test_cli_runner(mix_stderr=False)
