try:
    import urllib.request as urllib_request
    import urllib.error as urllib_error
except ImportError:
    import urllib2 as urllib_request
    import urllib2 as urllib_error
import json

from .api import TwitterCall, wrap_response

class TwitterJSONIter(object):

    def __init__(self, handle, uri, arg_data):
        self.decoder = json.JSONDecoder()
        self.handle = handle
        self.buf = ""

    def __iter__(self):
        while True:
            # This might need better py3 IO
            self.buf += self.handle.read(1024)
            try:
                res, ptr = self.decoder.raw_decode(self.buf)
                self.buf = self.buf[ptr + 2:] # +2 is for \r\n
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
    def __init__(
        self, domain="stream.twitter.com", secure=False, auth=None,
        api_version='1'):
        uriparts = ()
        uriparts += (str(api_version),)

        TwitterStreamCall.__init__(
            self, auth=auth, format="json", domain=domain,
            callable_cls=TwitterStreamCall,
            secure=secure, uriparts=uriparts)
