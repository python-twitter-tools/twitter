# encoding: utf-8
from __future__ import unicode_literals

try:
    import urllib.request as urllib_request
    import urllib.error as urllib_error
except ImportError:
    import urllib2 as urllib_request
    import urllib2 as urllib_error

try:
    from cStringIO import StringIO
except ImportError:
    from io import BytesIO as StringIO

from .twitter_globals import POST_ACTIONS
from .auth import NoAuth

import re
import sys
import gzip

try:
    import http.client as http_client
except ImportError:
    import httplib as http_client

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
        try:
            data = self.e.fp.read()
        except http_client.IncompleteRead as e:
            # can't read the error text
            # let's try some of it
            data = e.partial
        if self.e.headers.get('Content-Encoding') == 'gzip':
            buf = StringIO(data)
            f = gzip.GzipFile(fileobj=buf)
            self.response_data = f.read()
        else:
            self.response_data = data
        super(TwitterHTTPError, self).__init__(str(self))

    def __str__(self):
        fmt = ("." + self.format) if self.format else ""
        return (
            "Twitter sent status %i for URL: %s%s using parameters: "
            "(%s)\ndetails: %s" % (
                self.e.code, self.uri, fmt, self.uriparts,
                self.response_data))


class TwitterResponse(object):
    """
    Response from a twitter request. Behaves like a list or a string
    (depending on requested format) but it has a few other interesting
    attributes.

    `headers` gives you access to the response headers as an
    httplib.HTTPHeaders instance. You can do
    `response.headers.get('h')` to retrieve a header.
    """

    @property
    def rate_limit_remaining(self):
        """
        Remaining requests in the current rate-limit.
        """
        return int(self.headers.get('X-Rate-Limit-Remaining', "0"))

    @property
    def rate_limit_limit(self):
        """
        The rate limit ceiling for that given request.
        """
        return int(self.headers.get('X-Rate-Limit-Limit', "0"))

    @property
    def rate_limit_reset(self):
        """
        Time in UTC epoch seconds when the rate limit will reset.
        """
        return int(self.headers.get('X-Rate-Limit-Reset', "0"))


class TwitterDictResponse(dict, TwitterResponse):
    pass


class TwitterListResponse(list, TwitterResponse):
    pass


def wrap_response(response, headers):
    response_typ = type(response)
    if response_typ is dict:
        res = TwitterDictResponse(response)
        res.headers = headers
    elif response_typ is list:
        res = TwitterListResponse(response)
        res.headers = headers
    else:
        res = response
    return res

def method_for_uri(uri):
    method = "GET"
    for action in POST_ACTIONS:
        if re.search("%s(/\d+)?$" % action, uri):
            method = "POST"
            break
    return method

class TwitterCall(object):

    def __init__(
            self, auth, format, domain, callable_cls, uri="",
            uriparts=None, secure=True, timeout=None, gzip=False):
        self.auth = auth
        self.format = format
        self.domain = domain
        self.callable_cls = callable_cls
        self.uri = uri
        self.uriparts = uriparts
        self.secure = secure
        self.timeout = timeout
        self.gzip = gzip

    def __getattr__(self, k):
        try:
            return object.__getattr__(self, k)
        except AttributeError:
            def extend_call(arg):
                return self.callable_cls(
                    auth=self.auth, format=self.format, domain=self.domain,
                    callable_cls=self.callable_cls, timeout=self.timeout,
                    secure=self.secure, gzip=self.gzip,
                    uriparts=self.uriparts + (arg,))
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

        method = kwargs.pop('_method', None) or method_for_uri(uri)

        # If an id kwarg is present and there is no id to fill in in
        # the list of uriparts, assume the id goes at the end.
        id = kwargs.pop('id', None)
        if id:
            uri += "/%s" % (id)

        # If an _id kwarg is present, this is treated as id as a CGI
        # param.
        _id = kwargs.pop('_id', None)
        if _id:
            kwargs['id'] = _id

        # If an _timeout is specified in kwargs, use it
        _timeout = kwargs.pop('_timeout', None)

        secure_str = ''
        if self.secure:
            secure_str = 's'
        dot = ""
        if self.format:
            dot = "."
        uriBase = "http%s://%s/%s%s%s" % (
            secure_str, self.domain, uri, dot, self.format)

        # Check if argument tells whether img is already base64 encoded
        b64_convert = True
        if "_base64" in kwargs:
            b64_convert = not kwargs.pop("_base64")
        if b64_convert:
            import base64

        # Catch media arguments to handle oauth query differently for multipart
        media = None
        for arg in ['media[]']:
            if arg in kwargs:
                media = kwargs.pop(arg)
                if b64_convert:
                    media = base64.b64encode(media)
                if sys.version_info >= (3, 0):
                    media = str(media, 'utf8')
                mediafield = arg
                break

        # Catch media arguments that are not accepted through multipart
        # and are not yet base64 encoded
        if b64_convert:
            for arg in ['banner', 'image']:
                if arg in kwargs:
                    kwargs[arg] = base64.b64encode(kwargs[arg])

        headers = {'Accept-Encoding': 'gzip'} if self.gzip else dict()
        body = None
        arg_data = None
        if self.auth:
            headers.update(self.auth.generate_headers())
            # Use urlencoded oauth args with no params when sending media
            # via multipart and send it directly via uri even for post
            arg_data = self.auth.encode_params(
                uriBase, method, {} if media else kwargs)
            if method == 'GET' or media:
                uriBase += '?' + arg_data
            else:
                body = arg_data.encode('utf8')

        # Handle query as multipart when sending media
        if media:
            BOUNDARY = "###Python-Twitter###"
            bod = []
            bod.append('--' + BOUNDARY)
            bod.append(
                'Content-Disposition: form-data; name="%s"' % mediafield)
            bod.append('Content-Transfer-Encoding: base64')
            bod.append('')
            bod.append(media)
            for k, v in kwargs.items():
                bod.append('--' + BOUNDARY)
                bod.append('Content-Disposition: form-data; name="%s"' % k)
                bod.append('')
                bod.append(v)
            bod.append('--' + BOUNDARY + '--')
            body = '\r\n'.join(bod).encode('utf8')
            headers['Content-Type'] = \
                'multipart/form-data; boundary=%s' % BOUNDARY

        req = urllib_request.Request(uriBase, body, headers)
        return self._handle_response(req, uri, arg_data, _timeout)

    def _handle_response(self, req, uri, arg_data, _timeout=None):
        kwargs = {}
        if _timeout:
            kwargs['timeout'] = _timeout
        try:
            handle = urllib_request.urlopen(req, **kwargs)
            if handle.headers['Content-Type'] in ['image/jpeg', 'image/png']:
                return handle
            try:
                data = handle.read()
            except http_client.IncompleteRead as e:
                # Even if we don't get all the bytes we should have there
                # may be a complete response in e.partial
                data = e.partial
            if handle.info().get('Content-Encoding') == 'gzip':
                # Handle gzip decompression
                buf = StringIO(data)
                f = gzip.GzipFile(fileobj=buf)
                data = f.read()
            if len(data) == 0:
                return wrap_response({}, handle.headers)
            elif "json" == self.format:
                res = json.loads(data.decode('utf8'))
                return wrap_response(res, handle.headers)
            else:
                return wrap_response(
                    data.decode('utf8'), handle.headers)
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

    The Twitter API is documented at:

      http://dev.twitter.com/doc


    Examples::

        from twitter import *

        t = Twitter(
            auth=OAuth(token, token_key, con_secret, con_secret_key)))

        # Get your "home" timeline
        t.statuses.home_timeline()

        # Get a particular friend's timeline
        t.statuses.user_timeline(screen_name="billybob")

        # to pass in GET/POST parameters, such as `count`
        t.statuses.home_timeline(count=5)

        # to pass in the GET/POST parameter `id` you need to use `_id`
        t.statuses.oembed(_id=1234567890)

        # Update your status
        t.statuses.update(
            status="Using @sixohsix's sweet Python Twitter Tools.")

        # Send a direct message
        t.direct_messages.new(
            user="billybob",
            text="I think yer swell!")

        # Get the members of tamtar's list "Things That Are Rad"
        t._("tamtar")._("things-that-are-rad").members()

        # Note how the magic `_` method can be used to insert data
        # into the middle of a call. You can also use replacement:
        t.user.list.members(user="tamtar", list="things-that-are-rad")

        # An *optional* `_timeout` parameter can also be used for API
        # calls which take much more time than normal or twitter stops
        # responding for some reason:
        t.users.lookup(
            screen_name=','.join(A_LIST_OF_100_SCREEN_NAMES), \
            _timeout=1)

        # Overriding Method: GET/POST
        # you should not need to use this method as this library properly
        # detects whether GET or POST should be used, Nevertheless
        # to force a particular method, use `_method`
        t.statuses.oembed(_id=1234567890, _method='GET')

        # Send a tweet with an image included (or set your banner or logo similarily)
        # by just reading your image from the web or a file in a string:
        with open("example.png", "rb") as imagefile:
            params = {"media[]": imagefile.read(), "status": "PTT"}
        t.statuses.update_with_media(**params)

        # Or by sending a base64 encoded image:
        params = {"media[]": base64_image, "status": "PTT", "_base64": True}
        t.statuses.update_with_media(**params)


    Searching Twitter::

        # Search for the latest tweets about #pycon
        t.search.tweets(q="#pycon")


    Using the data returned
    -----------------------

    Twitter API calls return decoded JSON. This is converted into
    a bunch of Python lists, dicts, ints, and strings. For example::

        x = twitter.statuses.home_timeline()

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
        default it's `api.twitter.com`.

        If `secure` is False you will connect with HTTP instead of
        HTTPS.

        `api_version` is used to set the base uri. By default it's
        '1.1'.
        """
        if not auth:
            auth = NoAuth()

        if (format not in ("json", "xml", "")):
            raise ValueError("Unknown data format '%s'" % (format))

        if api_version is _DEFAULT:
            api_version = '1.1'

        uriparts = ()
        if api_version:
            uriparts += (str(api_version),)

        TwitterCall.__init__(
            self, auth=auth, format=format, domain=domain,
            callable_cls=TwitterCall,
            secure=secure, uriparts=uriparts)


__all__ = ["Twitter", "TwitterError", "TwitterHTTPError", "TwitterResponse"]
