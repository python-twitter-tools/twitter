import urllib
from base64 import encodestring

class Auth:
    def encode_params(self, base_url, method, params):
        """Encodes parameters for a request suitable for including in a URL
        or POST body.  This method may also add new params to the request
        if required by the authentication scheme in use."""
        raise NotImplementedError

    def generate_headers(self):
        """Generates headers which should be added to the request if required
        by the authentication scheme in use."""
        raise NotImplementedError

# An implementation using username and password.
class UserPassAuth(Auth):
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def encode_params(self, base_url, method, params):
        # We could consider automatically converting unicode to utf8 strings
        # before encoding...
        return urllib.urlencode(params)

    def generate_headers(self):
        return {"Authorization": "Basic " + encodestring("%s:%s" %(
                self.username, self.password)).strip('\n')}

class NoAuth(UserPassAuth):
    def __init__(self):
        pass

    def generate_headers(self):
        return {}
