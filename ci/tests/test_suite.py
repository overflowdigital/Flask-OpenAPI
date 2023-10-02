from flex import load as validate_fully
from flex.core import validate


def test_suite_validate_specs(test_data):
    mod, client, specs_data, opts = test_data
    skip_full_validation = opts.get("skip_full_validation", False)
    for url, spec in specs_data.items():
        if "openapi" not in spec and not skip_full_validation:
            # Flex can do a sophisticated and thorough validatation of
            # Swagger 2.0 specs, before it was renamed to OpenAPI.
            validate_fully(spec)
        else:
            # OpenAPI specs are not yet supported by flex, so we should fall
            # back to a fairly simple structural validation.
            validate(spec)


def test_suite_required_attributes(test_data):
    mod, client, specs_data, opts = test_data
    for url, spec in specs_data.items():
        assert "paths" in spec, "paths is required"
        assert "info" in spec, "info is required"


def test_suite_swag(test_data):
    mod, client, specs_data, opts = test_data
    if getattr(mod, "test_swag", None) is not None:
        mod.test_swag(client, specs_data)
