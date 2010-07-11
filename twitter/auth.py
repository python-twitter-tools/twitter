import urllib
from base64 import encodestring

class Auth(object):
    """
    ABC for Authenticator objects.
    """

    def encode_params(self, base_url, method, params):
        """Encodes parameters for a request suitable for including in a URL
        or POST body.  This method may also add new params to the request
        if required by the authentication scheme in use."""
        raise NotImplementedError()

    def generate_headers(self):
        """Generates headers which should be added to the request if required
        by the authentication scheme in use."""
        raise NotImplementedError()


class NoAuth(Auth):
    """
    No authentication authenticator.
    """
    def __init__(self):
        pass

    def encode_params(self, base_url, method, params):
        return urllib.urlencode(params)

    def generate_headers(self):
        return {}
