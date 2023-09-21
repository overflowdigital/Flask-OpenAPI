# DO NOT CHANGE MANUALLY THIS IS CHANGED IN THE PIPELINES
__version__ = "1.3.2"
# Based on works of Bruno Rocha and the Flasgger open source community


from jsonschema import ValidationError

from flask_openapi.openapi import (Flasgger, Swagger, OpenAPI)
from flask_openapi.core.decorators import swag_from
from flask_openapi.core.marshmallow_apispec import (APISpec, Schema,
                                                    SwaggerView, fields)
from flask_openapi.core.specs import apispec_to_template
from flask_openapi.core.validation import validate
from flask_openapi.utils.constants import OPTIONAL_FIELDS
from flask_openapi.utils.sanitizers import BR_SANITIZER, MK_SANITIZER, NO_SANITIZER
