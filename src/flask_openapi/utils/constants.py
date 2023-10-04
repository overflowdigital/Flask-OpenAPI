from typing import Any

OPTIONAL_FIELDS: list[str] = [
    "tags",
    "consumes",
    "produces",
    "schemes",
    "security",
    "deprecated",
    "operationId",
    "externalDocs",
]

OPTIONAL_OAS3_FIELDS: list[str] = ["components", "servers"]

OAS3_SUB_COMPONENTS: list[str] = [
    "parameters",
    "securitySchemes",
    "requestBodies",
    "responses",
    "headers",
    "examples",
    "links",
    "callbacks",
    "schemas",
]

DEFAULT_FIELDS: dict[str, Any] = {
    "tags": [],
    "consumes": ["application/json"],
    "produces": ["application/json"],
    "schemes": [],
    "security": [],
    "deprecated": False,
    "operationId": "",
    "definitions": {},
    "responses": {},
    "summary": None,
    "description": None,
    "parameters": [],
}
