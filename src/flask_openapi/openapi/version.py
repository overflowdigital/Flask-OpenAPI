from typing import Optional


def is_openapi3(openapi_version: Optional[str]) -> bool:
    """
    Returns True if openapi_version is 3
    """
    return openapi_version is not None and str(openapi_version).split(".")[0] == "3"
