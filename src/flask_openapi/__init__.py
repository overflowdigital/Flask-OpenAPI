# DO NOT CHANGE MANUALLY THIS IS CHANGED IN THE PIPELINES
# 9.9.9 is required to build locally (bit of a hack)
__version__ = "9.9.9"

# Based on works of Bruno Rocha and the Flasgger open source community


from flask_openapi.core.decorators import openapi_spec, swag_from  # noqa: F401
from flask_openapi.core.marshmallow_apispec import (  # noqa: F401
    APISpec,
    fields,
    Schema,
    SwaggerView,
)
from flask_openapi.core.specs import apispec_to_template  # noqa: F401
from flask_openapi.core.validation import validate  # noqa: F401
from flask_openapi.openapi import Flasgger, OpenAPI, Swagger  # noqa: F401
from flask_openapi.utils.constants import OPTIONAL_FIELDS  # noqa: F401
from flask_openapi.utils.files import load_from_file  # noqa: F401
from flask_openapi.utils.sanitizers import (  # noqa: F401
    BR_SANITIZER,
    MK_SANITIZER,
    NO_SANITIZER,
)
from jsonschema import ValidationError  # noqa: F401
