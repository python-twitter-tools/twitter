from requests.auth import HTTPBasicAuth


def UserPassAuth(username, password):
    """
    Basic auth authentication using email/username and
    password. Deprecated.
    """
    return HTTPBasicAuth(username, password)


def NoAuth():
    """
    No authentication authenticator.
    """
    return None

