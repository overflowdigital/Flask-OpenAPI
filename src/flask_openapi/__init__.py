# DO NOT CHANGE MANUALLY THIS IS CHANGED IN THE PIPELINES
__version__ = "1.3.2"
# Based on works of Bruno Rocha and the Flasgger open source community


from jsonschema import ValidationError

from .base import BR_SANITIZER, MK_SANITIZER, NO_SANITIZER, Flasgger, Swagger
from .core.decorators import swag_from  # noqa
from .core.marshmallow_apispec import (APISpec, Schema, SwaggerView,  # noqa
                                       fields)
from .core.specs import apispec_to_template  # noqa
from .core.validation import validate
from .utils.constants import OPTIONAL_FIELDS  # noqa
