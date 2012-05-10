try:
    import urllib.request as urllib_request
    import urllib.error as urllib_error
except ImportError:
    import urllib2 as urllib_request
    import urllib2 as urllib_error

from twitter.twitter_globals import POST_ACTIONS
from twitter.auth import NoAuth

import re

try:
    import json
except ImportError:
    import simplejson as json

class _DEFAULT(object):
    pass

class TwitterError(Exception):
    """
    Base Exception thrown by the Twitter object when there is a
    general error interacting with the API.
    """
    pass

class TwitterHTTPError(TwitterError):
    """
    Exception thrown by the Twitter object when there is an
    HTTP error interacting with twitter.com.
    """
    def __init__(self, e, uri, format, uriparts):
        self.e = e
        self.uri = uri
        self.format = format
        self.uriparts = uriparts
        self.response_data = self.e.fp.read()

    def __str__(self):
        fmt = ("." + self.format) if self.format else ""
        return (
            "Twitter sent status %i for URL: %s%s using parameters: "
            "(%s)\ndetails: %s" %(
                self.e.code, self.uri, fmt, self.uriparts,
                self.response_data))

class TwitterResponse(object):
    """
    Response from a twitter request. Behaves like a list or a string
    (depending on requested format) but it has a few other interesting
    attributes.

    `headers` gives you access to the response headers as an
    httplib.HTTPHeaders instance. You can do
    `response.headers.getheader('h')` to retrieve a header.
    """
    def __init__(self, headers):
        self.headers = headers

    @property
    def rate_limit_remaining(self):
        """
        Remaining requests in the current rate-limit.
        """
        return int(self.headers.getheader('X-RateLimit-Remaining'))

    @property
    def rate_limit_reset(self):
        """
        Time in UTC epoch seconds when the rate limit will reset.
        """
        return int(self.headers.getheader('X-RateLimit-Reset'))


def wrap_response(response, headers):
    response_typ = type(response)
    if response_typ is bool:
        # HURF DURF MY NAME IS PYTHON AND I CAN'T SUBCLASS bool.
        response_typ = int

    class WrappedTwitterResponse(response_typ, TwitterResponse):
        __doc__ = TwitterResponse.__doc__

        def __init__(self, response, headers):
            response_typ.__init__(self, response)
            TwitterResponse.__init__(self, headers)
        def __new__(cls, response, headers):
            return response_typ.__new__(cls, response)


    return WrappedTwitterResponse(response, headers)



class TwitterCall(object):

    def __init__(
        self, auth, format, domain, callable_cls, uri="",
        uriparts=None, secure=True):
        self.auth = auth
        self.format = format
        self.domain = domain
        self.callable_cls = callable_cls
        self.uri = uri
        self.uriparts = uriparts
        self.secure = secure

    def __getattr__(self, k):
        try:
            return object.__getattr__(self, k)
        except AttributeError:
            def extend_call(arg):
                return self.callable_cls(
                    auth=self.auth, format=self.format, domain=self.domain,
                    callable_cls=self.callable_cls, uriparts=self.uriparts \
                        + (arg,),
                    secure=self.secure)
            if k == "_":
                return extend_call
            else:
                return extend_call(k)

    def __call__(self, **kwargs):
        # Build the uri.
        uriparts = []
        for uripart in self.uriparts:
            # If this part matches a keyword argument, use the
            # supplied value otherwise, just use the part.
            uriparts.append(str(kwargs.pop(uripart, uripart)))
        uri = '/'.join(uriparts)

        method = kwargs.pop('_method', None)
        if not method:
            method = "GET"
            for action in POST_ACTIONS:
                if re.search("%s(/\d+)?$" % action, uri):
                    method = "POST"
                    break

        # If an id kwarg is present and there is no id to fill in in
        # the list of uriparts, assume the id goes at the end.
        id = kwargs.pop('id', None)
        if id:
            uri += "/%s" %(id)

        secure_str = ''
        if self.secure:
            secure_str = 's'
        dot = ""
        if self.format:
            dot = "."
        uriBase = "http%s://%s/%s%s%s" %(
                    secure_str, self.domain, uri, dot, self.format)

        headers = {}
        if self.auth:
            headers.update(self.auth.generate_headers())
            arg_data = self.auth.encode_params(uriBase, method, kwargs)
            if method == 'GET':
                uriBase += '?' + arg_data
                body = None
            else:
                body = arg_data.encode('utf8')

        req = urllib_request.Request(uriBase, body, headers)
        return self._handle_response(req, uri, arg_data)

    def _handle_response(self, req, uri, arg_data):
        try:
            handle = urllib_request.urlopen(req)
            if "json" == self.format:
                res = json.loads(handle.read().decode('utf8'))
                return wrap_response(res, handle.headers)
            else:
                return wrap_response(
                    handle.read().decode('utf8'), handle.headers)
        except urllib_error.HTTPError as e:
            if (e.code == 304):
                return []
            else:
                raise TwitterHTTPError(e, uri, self.format, arg_data)

class Twitter(TwitterCall):
    """
    The minimalist yet fully featured Twitter API class.

    Get RESTful data by accessing members of this class. The result
    is decoded python objects (lists and dicts).

    The Twitter API is documented here:

      http://dev.twitter.com/doc


    Examples::

      twitter = Twitter(
          auth=OAuth(token, token_key, con_secret, con_secret_key)))

      # Get the public timeline
      twitter.statuses.public_timeline()

      # Get a particular friend's timeline
      twitter.statuses.friends_timeline(id="billybob")

      # Also supported (but totally weird)
      twitter.statuses.friends_timeline.billybob()

      # Send a direct message
      twitter.direct_messages.new(
          user="billybob",
          text="I think yer swell!")

      # Get the members of a particular list of a particular friend
      twitter.user.listname.members(user="billybob", listname="billysbuds")


    Searching Twitter::

      twitter_search = Twitter(domain="search.twitter.com")

      # Find the latest search trends
      twitter_search.trends()

      # Search for the latest News on #gaza
      twitter_search.search(q="#gaza")


    Using the data returned
    -----------------------

    Twitter API calls return decoded JSON. This is converted into
    a bunch of Python lists, dicts, ints, and strings. For example::

      x = twitter.statuses.public_timeline()

      # The first 'tweet' in the timeline
      x[0]

      # The screen name of the user who wrote the first 'tweet'
      x[0]['user']['screen_name']


    Getting raw XML data
    --------------------

    If you prefer to get your Twitter data in XML format, pass
    format="xml" to the Twitter object when you instantiate it::

      twitter = Twitter(format="xml")

      The output will not be parsed in any way. It will be a raw string
      of XML.

    """
    def __init__(
        self, format="json",
        domain="api.twitter.com", secure=True, auth=None,
        api_version=_DEFAULT):
        """
        Create a new twitter API connector.

        Pass an `auth` parameter to use the credentials of a specific
        user. Generally you'll want to pass an `OAuth`
        instance::

            twitter = Twitter(auth=OAuth(
                    token, token_secret, consumer_key, consumer_secret))


        `domain` lets you change the domain you are connecting. By
        default it's `api.twitter.com` but `search.twitter.com` may be
        useful too.

        If `secure` is False you will connect with HTTP instead of
        HTTPS.

        `api_version` is used to set the base uri. By default it's
        '1'. If you are using "search.twitter.com" set this to None.
        """
        if not auth:
            auth = NoAuth()

        if (format not in ("json", "xml", "")):
            raise ValueError("Unknown data format '%s'" %(format))

        if api_version is _DEFAULT:
            if domain == 'api.twitter.com':
                api_version = '1'
            else:
                api_version = None

        uriparts = ()
        if api_version:
            uriparts += (str(api_version),)

        TwitterCall.__init__(
            self, auth=auth, format=format, domain=domain,
            callable_cls=TwitterCall,
            secure=secure, uriparts=uriparts)


__all__ = ["Twitter", "TwitterError", "TwitterHTTPError", "TwitterResponse"]
