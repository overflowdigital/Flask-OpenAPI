from typing import Any, Dict, List

OPTIONAL_FIELDS: List[str] = [
    "tags",
    "consumes",
    "produces",
    "schemes",
    "security",
    "deprecated",
    "operationId",
    "externalDocs",
]

OPTIONAL_OAS3_FIELDS: List[str] = ["components", "servers"]

OAS3_SUB_COMPONENTS: List[str] = [
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

DEFAULT_FIELDS: Dict[str, Any] = {
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
