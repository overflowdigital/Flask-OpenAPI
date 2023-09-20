# DO NOT CHANGE MANUALLY THIS IS CHANGED IN THE PIPELINES
__version__ = "1.4.0"

import flask_openapi.compat.marshmallow as marshmallow_shim  # noqa
from flask_openapi.core import OpenAPI  # noqa
from flask_openapi.core import Swagger  # noqa
from flask_openapi.core import Flasgger  # noqa
from flask_openapi.openapi.specs import apispec_to_template  # noqa
from flask_openapi.utils.decorators import swag_from  # noqa
from flask_openapi.utils.sanitizers import BR_SANITIZER  # noqa
from flask_openapi.utils.sanitizers import MK_SANITIZER  # noqa
from flask_openapi.utils.sanitizers import NO_SANITIZER  # noqa
from flask_openapi.openapi.validator import validate  # noqa
