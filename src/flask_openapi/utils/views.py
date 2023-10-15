from typing import Any, Callable, Dict

from flask.views import MethodView


def has_valid_dispatch_view_docs(endpoint: Callable) -> bool:
    """
    Return True if dispatch_request is swaggable

    :param endpoint: endpoint
    :type endpoint: Callable

    :return: True if dispatch_request is swaggable
    :rtype: bool
    """
    klass: Any = endpoint.__dict__.get("view_class", None)
    return (
        klass
        and hasattr(klass, "dispatch_request")
        and hasattr(endpoint, "methods")
        and getattr(klass, "dispatch_request").__doc__
    )


def get_vendor_extension_fields(mapping: Dict) -> Dict[str, Any]:
    """
    Identify vendor extension fields and extract them into a new dictionary.
    Examples:
        >>> get_vendor_extension_fields({'test': 1})
        {}
        >>> get_vendor_extension_fields({'test': 1, 'x-test': 2})
        {'x-test': 2}

    :param mapping: dictionary to extract vendor extension fields from
    :type mapping: dict

    :return: dictionary of vendor extension fields
    :rtype: dict
    """
    return {k: v for k, v in mapping.items() if k.startswith("x-")}


def is_valid_method_view(endpoint: Callable) -> bool:
    """
    Return True if obj is MethodView

    :param endpoint: endpoint
    :type endpoint: Callable

    :return: True if obj is MethodView
    :rtype: bool
    """
    klass: Any = endpoint.__dict__.get("view_class", None)
    try:
        return issubclass(klass, MethodView)
    except TypeError:
        return False
