def is_openapi3(openapi_version: str) -> bool:
    """
    Returns True if openapi_version is 3

    :param openapi_version: openapi version
    :type openapi_version: str

    :return: True if openapi_version is 3
    :rtype: bool
    """
    return openapi_version and str(openapi_version).split(".")[0] == "3"
