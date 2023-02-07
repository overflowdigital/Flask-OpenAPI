import codecs
import json
import os
from typing import Any, Callable

from flask import Flask

from flask_openapi.openapi.parsers import parse_imports

import yaml


def load_swagger_file(app: Flask, filename: str) -> Any:
    loader: Callable = lambda stream: yaml.safe_load(
        parse_imports(stream.read(), filename)
    )  # noqa

    if not filename.startswith("/"):
        filename: str = os.path.join(app.root_path, filename)

    if filename.endswith(".json"):
        loader = json.load
    else:
        with codecs.open(filename, "r", "utf-8") as f:
            contents: str = f.read().strip()
            if contents[0] in ["{", "["]:
                loader = json.load

            return loader(f)

    with codecs.open(filename, "r", "utf-8") as f:
        return loader(f)
