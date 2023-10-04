from typing import Optional, Union


def is_openapi3(openapi_version: Optional[Union[str, int]]) -> bool:
    """
    Returns True if openapi_version is 3

    :param openapi_version: openapi version
    :type openapi_version: str | int | None

    :return: True if openapi_version is 3
    :rtype: bool
    """
    return openapi_version is not None and str(openapi_version).split(".")[0] == "3"
