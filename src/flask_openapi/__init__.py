# DO NOT CHANGE MANUALLY THIS IS CHANGED IN THE PIPELINES
# 9.9.9 is required to build locally (bit of a hack)
__version__ = "9.9.9"

# Based on works of Bruno Rocha and the Flasgger open source community


from jsonschema import ValidationError

from flask_openapi.core.decorators import openapi_spec, swag_from
from flask_openapi.core.marshmallow_apispec import APISpec, Schema, SwaggerView, fields
from flask_openapi.core.specs import apispec_to_template
from flask_openapi.core.validation import validate
from flask_openapi.openapi import Flasgger, OpenAPI, Swagger
from flask_openapi.utils.constants import OPTIONAL_FIELDS
from flask_openapi.utils.sanitizers import BR_SANITIZER, MK_SANITIZER, NO_SANITIZER
