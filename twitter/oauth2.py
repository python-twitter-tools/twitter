"""
Twitter only supports the application-only flow of OAuth2 for certain
API endpoints. This OAuth2 authenticator only supports the application-only
flow right now.

To authenticate with OAuth2, visit the Twitter developer page and create a new
application:

    https://dev.twitter.com/apps/new

This will get you a CONSUMER_KEY and CONSUMER_SECRET.

Exchange your CONSUMER_KEY and CONSUMER_SECRET for a bearer token using the
oauth2_dance function.

Finally, you can use the OAuth2 authenticator and your bearer token to connect
to Twitter. In code it goes like this::

    twitter = Twitter(auth=OAuth2(bearer_token=BEARER_TOKEN))

    # Now work with Twitter
    twitter.search.tweets(q='keyword')

"""

from __future__ import print_function

try:
    from urllib.parse import quote, urlencode
except ImportError:
    from urllib import quote, urlencode

from base64 import b64encode
from .auth import Auth

def write_bearer_token_file(filename, oauth2_bearer_token):
    """
    Write a token file to hold the oauth2 bearer token.
    """
    oauth_file = open(filename, 'w')
    print(oauth2_bearer_token, file=oauth_file)
    oauth_file.close()

def read_bearer_token_file(filename):
    """
    Read a token file and return the oauth2 bearer token.
    """
    f = open(filename)
    return f.readline().strip()

class OAuth2(Auth):
    """
    An OAuth2 application-only authenticator.
    """
    def __init__(self, consumer_key=None, consumer_secret=None,
                 bearer_token=None):
        """
        Create an authenticator. You can supply consumer_key and
        consumer_secret if you are requesting a bearer_token. Otherwise
        you must supply the bearer_token.
        """
        self.bearer_token = bearer_token
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret

        if not (bearer_token or (consumer_key and consumer_secret)):
            raise MissingCredentialsError(
                'You must supply either a bearer token, or both a '
                'consumer_key and a consumer_secret.')

    def encode_params(self, base_url, method, params):
        return urlencode(params)

    def generate_headers(self):
        if self.bearer_token:
            headers = {
                b'Authorization': 'Bearer {0}'.format(
                    self.bearer_token).encode('utf8')
            }
        else:
            headers = {
                b'Content-Type': (b'application/x-www-form-urlencoded;'
                                  b'charset=UTF-8'),
                b'Authorization': 'Basic {0}'.format(
                    b64encode('{0}:{1}'.format(
                        quote(self.consumer_key),
                        quote(self.consumer_secret)).encode('utf8')
                    ).decode('utf8')
                ).encode('utf8')
            }
        return headers


class MissingCredentialsError(Exception):
    pass
