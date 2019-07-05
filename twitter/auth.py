try:
    import urllib.parse as urllib_parse
    from base64 import encodebytes
except ImportError:
    import urllib as urllib_parse
    from base64 import encodestring as encodebytes


class Auth(object):
    """
    ABC for Authenticator objects.
    """

    def encode_params(self, base_url, method, params):
        """Encodes parameters for a request suitable for including in a URL
        or POST body.  This method may also add new params to the request
        if required by the authentication scheme in use."""
        raise NotImplementedError()

    def generate_headers(self, *args, **kwargs):
        """Generates headers which should be added to the request if required
        by the authentication scheme in use."""
        raise NotImplementedError()


class UserPassAuth(Auth):
    """
    Basic auth authentication using email/username and
    password. Deprecated.
    """
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def encode_params(self, base_url, method, params):
        # We could consider automatically converting unicode to utf8 strings
        # before encoding...
        return urllib_parse.urlencode(params)

    def generate_headers(self, *args, **kwargs):
        return {b"Authorization": b"Basic " + encodebytes(
                ("%s:%s" %(self.username, self.password))
                .encode('utf8')).strip(b'\n')
                }


class NoAuth(Auth):
    """
    No authentication authenticator.
    """
    def __init__(self):
        pass

    def encode_params(self, base_url, method, params):
        return urllib_parse.urlencode(params)

    def generate_headers(self, *args, **kwargs):
        return {}


class MissingCredentialsError(Exception):
    pass
