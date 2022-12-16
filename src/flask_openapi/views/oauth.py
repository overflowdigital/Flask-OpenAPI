from flask import render_template
from flask.views import MethodView


class OAuthRedirect(MethodView):
    """ The OAuth2 redirect HTML for Swagger UI standard/implicit flow """
    def get(self) -> str:
        return render_template(['flask_openapi/oauth2-redirect.html', 'flask_openapi/o2c.html'])
