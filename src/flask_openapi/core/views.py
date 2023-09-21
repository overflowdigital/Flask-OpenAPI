from flask_openapi import __version__


from flask import Response, jsonify, render_template, request, url_for
from flask.views import MethodView
from werkzeug.datastructures import Authorization


import json
from typing import Optional


class APIDocsView(MethodView):
    """
    The /apidocs
    """

    def __init__(self, *args, **kwargs):
        view_args = kwargs.pop("view_args", {})
        self.config = view_args.get("config")
        super(APIDocsView, self).__init__(*args, **kwargs)

    def get(self):
        """
        The data under /apidocs
        json or Swagger UI
        """

        do_auth: bool = self.config.get("pageProtection", False)
        is_auth: bool = True

        if do_auth:
            request_auth: Optional[Authorization] = request.authorization
            username: str = self.config.get("pageUsername", "")
            password: str = self.config.get("pagePassword", "")
            is_auth = (
                request_auth
                and request_auth.type == "basic"
                and request_auth.username == username
                and request_auth.password == password
            )  # noqa

        if is_auth:
            base_endpoint = self.config.get("endpoint", "flask_openapi")
            specs = [
                {
                    "url": url_for(".".join((base_endpoint, spec["endpoint"]))),
                    "title": spec.get("title", "API Spec 1"),
                    "name": spec.get("name", None),
                    "version": spec.get("version", "0.0.1"),
                    "endpoint": spec.get("endpoint"),
                }
                for spec in self.config.get("specs", [])
            ]
            urls = [
                {"name": spec["name"], "url": spec["url"]}
                for spec in specs
                if spec["name"]
            ]
            data = {
                "specs": specs,
                "urls": urls,
                "title": self.config.get("title", "API Docs"),
            }
            if request.args.get("json"):
                # calling with ?json returns specs
                return jsonify(data)
            else:  # pragma: no cover
                data["flasgger_config"] = self.config
                data["json"] = json
                data["flasgger_version"] = __version__
                data["favicon"] = self.config.get(
                    "favicon",
                    url_for("flask_openapi.static", filename="favicon-32x32.png"),
                )
                data["swagger_ui_bundle_js"] = self.config.get(
                    "swagger_ui_bundle_js",
                    url_for("flask_openapi.static", filename="swagger-ui-bundle.js"),
                )
                data["swagger_ui_standalone_preset_js"] = self.config.get(
                    "swagger_ui_standalone_preset_js",
                    url_for(
                        "flask_openapi.static",
                        filename="swagger-ui-standalone-preset.js",
                    ),
                )
                data["jquery_js"] = self.config.get(
                    "jquery_js",
                    url_for("flask_openapi.static", filename="lib/jquery.min.js"),
                )
                data["swagger_ui_css"] = self.config.get(
                    "swagger_ui_css",
                    url_for("flask_openapi.static", filename="swagger-ui.css"),
                )
                return render_template("flask_openapi/index.html", **data)
        else:
            return (
                "Unauthorized",
                401,
                {"WWW-Authenticate": 'Basic realm="OpenAPI Documentation"'},
            )


class OAuthRedirect(MethodView):
    """
    The OAuth2 redirect HTML for Swagger UI standard/implicit flow
    """

    def get(self):
        return render_template(
            ["flask_openapi/oauth2-redirect.html", "flask_openapi/o2c.html"],
        )


class APISpecsView(MethodView):
    """
    The /apispec_1.json and other specs
    """

    def __init__(self, *args, **kwargs):
        self.loader = kwargs.pop("loader")
        super(APISpecsView, self).__init__(*args, **kwargs)

    def get(self):
        """
        The Swagger view get method outputs to /apispecs_1.json
        """
        try:
            return jsonify(self.loader())
        except Exception:
            specs = json.dumps(self.loader())
            return Response(specs, mimetype="application/json")