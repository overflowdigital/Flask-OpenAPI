from flask_openapi.core import Swagger
from flask_openapi.constants import DEFAULT_CONFIG, DEFAULT_ENDPOINT
from flask_openapi.openapi.specs import get_apispecs

import pytest


def test_get_apispecs_with_invalid_endpoint(app):
    Swagger(app)

    with app.app_context():
        with pytest.raises(RuntimeError) as e:
            bad_endpoint = "Bad endpoint"
            get_apispecs(bad_endpoint)
            assert bad_endpoint in e


def test_get_apispecs_with_valid_endpoint(app):
    Swagger(app)
    with app.app_context():
        assert get_apispecs(DEFAULT_ENDPOINT)
