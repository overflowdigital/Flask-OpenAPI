import json
from typing import Optional, Union

from flask import Response, jsonify, render_template, request, url_for
from flask.views import MethodView

from flask_openapi import __version__
from flask_openapi.constants import (
    DEFAULT_BUNDLE_JS,
    DEFAULT_CSS,
    DEFAULT_FAVICON,
    DEFAULT_JQUERY,
    DEFAULT_PRESET_JS,
)

from werkzeug.datastructures import Authorization


def _is_auth(auth: Optional[Authorization], username: str, password: str) -> bool:
    return (
        auth is not None and 
        auth.type == "basic" and
        auth.username == username and
        auth.password == password
    )


def create_spec(spec: dict[str, str], endpoint: str) -> dict[str, str]:
    return {
        "url": url_for(".".join((endpoint, spec["endpoint"]))),
        "title": spec.get("title", "API Spec 1"),
        "name": spec.get("name", ""),
        "version": spec.get("version", "0.0.1"),
        "endpoint": spec.get("endpoint", ""),
    }


def create_url(spec: dict[str, str]) -> dict[str, str]:
    return {"name": spec.get("name", ""), "url": spec.get("url", "")}


def enrich_context(data: dict, config: dict) -> dict:
    data["flask_openapi_config"] = config
    data["json"] = json
    data["flask_openapi_version"] = __version__
    data["favicon"] = config.get(
        "favicon", url_for("flask_openapi.static", filename=DEFAULT_FAVICON)
    )
    data["swagger_ui_bundle_js"] = config.get(
        "swagger_ui_bundle_js",
        url_for("flask_openapi.static", filename=DEFAULT_BUNDLE_JS),
    )
    data["swagger_ui_standalone_preset_js"] = config.get(
        "swagger_ui_standalone_preset_js",
        url_for("flask_openapi.static", filename=DEFAULT_PRESET_JS),
    )
    data["jquery_js"] = config.get(
        "jquery_js", url_for("flask_openapi.static", filename=DEFAULT_JQUERY)
    )
    data["swagger_ui_css"] = config.get(
        "swagger_ui_css", url_for("flask_openapi.static", filename=DEFAULT_CSS)
    )

    return data


class APIDocsView(MethodView):
    """View that displays the SwaggerUI pages"""

    def __init__(self, *args: tuple, **kwargs: dict) -> None:
        view_args: dict = kwargs.pop("view_args", {})
        self.config: dict = view_args.get("config", {})
        super(APIDocsView, self).__init__(*args, **kwargs)

    def get(self) -> Union[Response, str, tuple[str, int, dict[str, str]]]:
        do_auth: bool = self.config.get("pageProtection", False)
        is_auth: bool = True

        if do_auth:
            request_auth: Optional[Authorization] = request.authorization
            username: str = self.config.get("pageUsername", "")
            password: str = self.config.get("pagePassword", "")
            is_auth = _is_auth(request_auth, username, password)

        if is_auth:
            base_endpoint: str = self.config.get("endpoint", "flask_openapi")
            specs: list[dict[str, str]] = [
                create_spec(spec, base_endpoint)
                for spec in self.config.get("specs", {})
            ]
            urls: list[dict[str, str]] = [
                create_url(spec) for spec in specs if spec["name"]
            ]
            data: dict = {
                "specs": specs,
                "urls": urls,
                "title": self.config.get("title", "API Docs"),
            }

            if request.args.get("json"):
                return jsonify(data)
            else:
                return render_template(
                    "flask_openapi/index.html", **enrich_context(data, self.config)
                )
        else:
            return (
                "Unauthorized",
                401,
                {"WWW-Authenticate": 'Basic realm="OpenAPI Documentation"'},
            )
