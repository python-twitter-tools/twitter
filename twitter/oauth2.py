"""
Visit the Twitter developer page and create a new application:

    https://dev.twitter.com/apps/new

This will get you a CONSUMER_KEY and CONSUMER_SECRET.

Twitter only supports the application-only flow of OAuth2 for certain
API endpoints. This OAuth2 authenticator only supports the application-only
flow right now. If twitter supports OAuth2 for other endpoints, this
authenticator may be modified as needed.

Finally, you can use the OAuth2 authenticator to connect to Twitter. In
code it all goes like this::

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
        self.bearer_token = None
        self.consumer_key = None
        self.consumer_secret = None

        if bearer_token:
            self.bearer_token = bearer_token
        elif consumer_key and consumer_secret:
            self.consumer_key = consumer_key
            self.consumer_secret = consumer_secret
        else:
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

        elif self.consumer_key and self.consumer_secret:

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

        else:
            raise MissingCredentialsError(
                'You must supply either a bearer token, or both a '
                'consumer_key and a consumer_secret.')

        return headers


class MissingCredentialsError(Exception):
    pass
