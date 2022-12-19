# DO NOT CHANGE MANUALLY THIS IS CHANGED IN THE PIPELINES
__version__ = '1.4.0'

import flask_openapi.compat.marshmallow as marshmallow_shim  # noqa
from flask_openapi.core import OpenAPI  # noqa
from flask_openapi.core import Swagger  # noqa
from flask_openapi.core import Flasgger  # noqa
from flask_openapi.utils import apispec_to_template  # noqa
from flask_openapi.utils.decorator import swag_from  # noqa
from flask_openapi.utils.encoder import LazyJSONEncoder  # noqa
from flask_openapi.utils.sanitizers import BR_SANITIZER  # noqa
from flask_openapi.utils.sanitizers import MK_SANITIZER  # noqa
from flask_openapi.utils.sanitizers import NO_SANITIZER  # noqa
from flask_openapi.utils.types import LazyString  # noqa
from flask_openapi.utils import validate  # noqa
