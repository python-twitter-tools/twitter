try:
    import urllib.request as urllib_request
    import urllib.error as urllib_error
    import io
except ImportError:
    import urllib2 as urllib_request
    import urllib2 as urllib_error
import json

from .api import TwitterCall, wrap_response

class TwitterJSONIter(object):

    def __init__(self, handle, uri, arg_data):
        self.decoder = json.JSONDecoder()
        self.handle = handle
        self.buf = b""

    def __iter__(self):
        while True:
            self.buf += self.handle.read(1024)
            try:
                utf8_buf = self.buf.decode('utf8').lstrip()
                res, ptr = self.decoder.raw_decode(utf8_buf)
                self.buf = utf8_buf[ptr:].encode('utf8')
                yield wrap_response(res, self.handle.headers)
            except ValueError as e:
                continue
            except urllib_error.HTTPError as e:
                raise TwitterHTTPError(e, uri, self.format, arg_data)

class TwitterStreamCall(TwitterCall):
    def _handle_response(self, req, uri, arg_data):
        handle = urllib_request.urlopen(req,)
        return iter(TwitterJSONIter(handle, uri, arg_data))

class TwitterStream(TwitterStreamCall):
    """
    Interface to the Twitter Stream API (stream.twitter.com). This can
    be used pretty much the same as the Twitter class except the
    result of calling a method will be an iterator that yields objects
    decoded from the stream. For example::

        twitter_stream = TwitterStream(auth=UserPassAuth('joe', 'joespassword'))
        iterator = twitter_stream.statuses.sample()

        for tweet in iterator:
            ...do something with this tweet...

    The iterator will yield tweets forever and ever (until the stream
    breaks at which point it raises a TwitterHTTPError.)
    """
    def __init__(
        self, domain="stream.twitter.com", secure=False, auth=None,
        api_version='1'):
        uriparts = ()
        uriparts += (str(api_version),)

        TwitterStreamCall.__init__(
            self, auth=auth, format="json", domain=domain,
            callable_cls=TwitterStreamCall,
            secure=secure, uriparts=uriparts)
