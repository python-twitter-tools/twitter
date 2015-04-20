"""
Visit the Twitter developer page and create a new application:

    https://dev.twitter.com/apps/new

This will get you a CONSUMER_KEY and CONSUMER_SECRET.

When users run your application they have to authenticate your app
with their Twitter account. A few HTTP calls to twitter are required
to do this. Please see the twitter.oauth_dance module to see how this
is done. If you are making a command-line app, you can use the
oauth_dance() function directly.

Performing the "oauth dance" gets you an ouath token and oauth secret
that authenticate the user with Twitter. You should save these for
later so that the user doesn't have to do the oauth dance again.

read_token_file and write_token_file are utility methods to read and
write OAuth token and secret key values. The values are stored as
strings in the file. Not terribly exciting.

Finally, you can use the OAuth authenticator to connect to Twitter. In
code it all goes like this::

    from twitter import *

    MY_TWITTER_CREDS = os.path.expanduser('~/.my_app_credentials')
    if not os.path.exists(MY_TWITTER_CREDS):
        oauth_dance("My App Name", CONSUMER_KEY, CONSUMER_SECRET,
                    MY_TWITTER_CREDS)

    oauth_token, oauth_secret = read_token_file(MY_TWITTER_CREDS)

    twitter = Twitter(auth=OAuth(
        oauth_token, oauth_token_secret, CONSUMER_KEY, CONSUMER_SECRET))

    # Now work with Twitter
    twitter.statuses.update(status='Hello, world!')

"""

from __future__ import print_function

from random import getrandbits
from time import time

from .util import PY_3_OR_HIGHER

try:
    import urllib.parse as urllib_parse
    from urllib.parse import urlencode
except ImportError:
    import urllib2 as urllib_parse
    from urllib import urlencode

import hashlib
import hmac
import base64

from .auth import Auth, MissingCredentialsError


def write_token_file(filename, oauth_token, oauth_token_secret):
    """
    Write a token file to hold the oauth token and oauth token secret.
    """
    oauth_file = open(filename, 'w')
    print(oauth_token, file=oauth_file)
    print(oauth_token_secret, file=oauth_file)
    oauth_file.close()

def read_token_file(filename):
    """
    Read a token file and return the oauth token and oauth token secret.
    """
    f = open(filename)
    return f.readline().strip(), f.readline().strip()


class OAuth(Auth):
    """
    An OAuth authenticator.
    """
    def __init__(self, token, token_secret, consumer_key, consumer_secret):
        """
        Create the authenticator. If you are in the initial stages of
        the OAuth dance and don't yet have a token or token_secret,
        pass empty strings for these params.
        """
        self.token = token
        self.token_secret = token_secret
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret

        if token_secret is None or consumer_secret is None:
            raise MissingCredentialsError(
                'You must supply strings for token_secret and consumer_secret, not None.')

    def encode_params(self, base_url, method, params):
        params = params.copy()

        if self.token:
            params['oauth_token'] = self.token

        params['oauth_consumer_key'] = self.consumer_key
        params['oauth_signature_method'] = 'HMAC-SHA1'
        params['oauth_version'] = '1.0'
        params['oauth_timestamp'] = str(int(time()))
        params['oauth_nonce'] = str(getrandbits(64))

        enc_params = urlencode_noplus(sorted(params.items()))

        key = self.consumer_secret + "&" + urllib_parse.quote(self.token_secret, safe='~')

        message = '&'.join(
            urllib_parse.quote(i, safe='~') for i in [method.upper(), base_url, enc_params])

        signature = (base64.b64encode(hmac.new(
                    key.encode('ascii'), message.encode('ascii'), hashlib.sha1)
                                      .digest()))
        return enc_params + "&" + "oauth_signature=" + urllib_parse.quote(signature, safe='~')

    def generate_headers(self):
        return {}

# apparently contrary to the HTTP RFCs, spaces in arguments must be encoded as
# %20 rather than '+' when constructing an OAuth signature (and therefore
# also in the request itself.)
# So here is a specialized version which does exactly that.
# In Python2, since there is no safe option for urlencode, we force it by hand
def urlencode_noplus(query):
    if not PY_3_OR_HIGHER:
        new_query = []
        TILDE = '____TILDE-PYTHON-TWITTER____'
        for k,v in query:
            if type(k) is unicode: k = k.encode('utf-8')
            k = str(k).replace("~", TILDE)
            if type(v) is unicode: v = v.encode('utf-8')
            v = str(v).replace("~", TILDE)
            new_query.append((k, v))
        query = new_query
        return urlencode(query).replace(TILDE, "~").replace("+", "%20")

    return urlencode(query, safe='~').replace("+", "%20")
