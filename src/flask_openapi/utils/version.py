def is_openapi3(openapi_version):
    """
    Returns True if openapi_version is 3
    """
    return openapi_version and str(openapi_version).split(".")[0] == "3"
