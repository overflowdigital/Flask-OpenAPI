from typing import Callable, Optional

from flask import current_app
from flask.views import MethodView

from werkzeug.routing import Rule


def has_valid_dispatch_view_docs(endpoint) -> bool:
    """
    Return True if dispatch_request is swaggable
    """
    klass = endpoint.__dict__.get("view_class", None)
    return (
        klass and hasattr(klass, "dispatch_request")
        and hasattr(endpoint, "methods")
        and getattr(klass, "dispatch_request").__doc__
    )  # noqa


def is_valid_method_view(endpoint) -> bool:
    """
    Return True if obj is MethodView
    """
    klass = endpoint.__dict__.get("view_class", None)
    try:
        return issubclass(klass, MethodView)
    except TypeError:
        return False


def get_url_mappings(rule_filter: Optional[Callable] = None) -> list[Rule]:
    """Returns all werkzeug rules"""
    rule_filter = rule_filter or (lambda rule: True)
    return [rule for rule in current_app.url_map.iter_rules() if rule_filter(rule)]
