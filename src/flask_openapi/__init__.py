# DO NOT CHANGE MANUALLY THIS IS CHANGED IN THE PIPELINES
__version__ = '1.4.0'
# Based on works of Bruno Rocha and the Flasgger open source community


from jsonschema import ValidationError  # noqa

from .base import (BR_SANITIZER, Flasgger, LazyJSONEncoder,  # noqa
                   MK_SANITIZER, NO_SANITIZER, Swagger)
from .constants import OPTIONAL_FIELDS  # noqa
from .marshmallow_apispec import APISpec, fields, Schema, SwaggerView  # noqa
from .utils import apispec_to_template, LazyString, swag_from, validate  # noqa
