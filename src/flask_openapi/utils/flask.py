from flask.views import MethodView


def has_valid_dispatch_view_docs(endpoint):
    """
    Return True if dispatch_request is swaggable
    """
    klass = endpoint.__dict__.get("view_class", None)
    return (
        klass
        and hasattr(klass, "dispatch_request")
        and hasattr(endpoint, "methods")
        and getattr(klass, "dispatch_request").__doc__
    )


def get_vendor_extension_fields(mapping):
    """
    Identify vendor extension fields and extract them into a new dictionary.
    Examples:
        >>> get_vendor_extension_fields({'test': 1})
        {}
        >>> get_vendor_extension_fields({'test': 1, 'x-test': 2})
        {'x-test': 2}
    """
    return {k: v for k, v in mapping.items() if k.startswith("x-")}


def is_valid_method_view(endpoint):
    """
    Return True if obj is MethodView
    """
    klass = endpoint.__dict__.get("view_class", None)
    try:
        return issubclass(klass, MethodView)
    except TypeError:
        return False
