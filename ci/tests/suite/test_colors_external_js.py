"""
The simple example using declared definitions, and external static js/css.
"""

from flask import Flask, jsonify

from flask_openapi import Swagger

app = Flask(__name__)
app.config["SWAGGER"] = {"title": "Colors API"}
swagger_config = Swagger.DEFAULT_CONFIG
swagger_config[
    "swagger_ui_bundle_js"
] = "//unpkg.com/swagger-ui-dist@3/swagger-ui-bundle.js"
swagger_config[
    "swagger_ui_standalone_preset_js"
] = "//unpkg.com/swagger-ui-dist@3/swagger-ui-standalone-preset.js"
swagger_config["jquery_js"] = "//unpkg.com/jquery@2.2.4/dist/jquery.min.js"
swagger_config["swagger_ui_css"] = "//unpkg.com/swagger-ui-dist@3/swagger-ui.css"
Swagger(app, config=swagger_config)


@app.route("/colors/<palette>/")
def colors(palette):
    """Example endpoint return a list of colors by palette
    This is using docstring for specifications
    ---
    tags:
      - colors
    parameters:
      - name: palette
        in: path
        type: string
        enum: ['all', 'rgb', 'cmyk']
        required: true
        default: all
        description: Which palette to filter?
    operationId: get_colors
    consumes:
      - application/json
    produces:
      - application/json
    security:
      colors_auth:
        - 'write:colors'
        - 'read:colors'
    schemes: ['http', 'https']
    deprecated: false
    externalDocs:
      description: Project repository
      url: http://github.com/overflowdigital/flask-openapi
    definitions:
      Palette:
        type: object
        properties:
          palette_name:
            type: array
            items:
              $ref: '#/definitions/Color'
      Color:
        type: string
    responses:
      200:
        description: A list of colors (may be filtered by palette)
        schema:
          $ref: '#/definitions/Palette'
        examples:
          rgb: ['red', 'green', 'blue']
    """
    all_colors = {
        "cmyk": ["cyan", "magenta", "yellow", "black"],
        "rgb": ["red", "green", "blue"],
    }
    if palette == "all":
        result = all_colors
    else:
        result = {palette: all_colors.get(palette)}

    return jsonify(result)


def test_swag(client, specs_data):
    """
    :param client: Flask app test client
    :param specs_data: {'url': {swag_specs}} for every spec in app
    """
    for url, spec in specs_data.items():
        assert "Palette" in spec["definitions"]
        assert "Color" in spec["definitions"]
        assert "colors" in spec["paths"]["/colors/{palette}/"]["get"]["tags"]


if __name__ == "__main__":
    app.run(debug=True)
