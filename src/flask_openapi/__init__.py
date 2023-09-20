# DO NOT CHANGE MANUALLY THIS IS CHANGED IN THE PIPELINES
__version__ = "1.3.2"
# Based on works of Bruno Rocha and the Flasgger open source community


from jsonschema import ValidationError

from .core.validation import validate

from .core.decorators import swag_from  # noqa

from .base import (
    BR_SANITIZER,
    Flasgger,
    MK_SANITIZER,
    NO_SANITIZER,
    Swagger,
)
from .constants import OPTIONAL_FIELDS  # noqa
from .marshmallow_apispec import APISpec, fields, Schema, SwaggerView  # noqa
from .core.specs import apispec_to_template  # noqa
