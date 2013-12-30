try:
    import urllib.request as urllib_request
    import urllib.error as urllib_error
    import io
except ImportError:
    import urllib2 as urllib_request
    import urllib2 as urllib_error
import json
from ssl import SSLError
import socket
import sys, select, time

from .api import TwitterCall, wrap_response, TwitterHTTPError

class TwitterJSONIter(object):

    def __init__(self, handle, uri, arg_data, block=True,
                 timeout=None, display_sizes=False):
        self.uri = uri
        self.arg_data = arg_data
        self.decoder = json.JSONDecoder()
        self.handle = handle
        self.buf = b""
        self.block = block
        self.timeout = timeout
        self.timer = time.time()
        self.display_sizes = display_sizes

    def __iter__(self):
        if sys.version_info >= (3, 0):
            sock = self.handle.fp.raw._sock
        else:
            sock = self.handle.fp._sock.fp._sock
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        if not self.block or self.timeout:
            sock.setblocking(False)
        while True:
            utf8_buf = self.buf.decode('utf8').lstrip()
            pos = utf8_buf.find('{')
            if pos != -1:
                if self.display_sizes:
                    for size in utf8_buf[:pos].split('\n'):
                        yield wrap_response(size.strip(), self.handle.headers)
                utf8_buf = utf8_buf[pos:]
                self.buf = utf8_buf.encode('utf-8')
            try:
                res, ptr = self.decoder.raw_decode(utf8_buf)
                self.buf = utf8_buf[ptr:].encode('utf8')
                if isinstance(res, dict) or self.display_sizes:
                    yield wrap_response(res, self.handle.headers)
                self.timer = time.time()
                continue
            except ValueError as e:
                if self.block and not self.timeout:
                    pass
                else:
                    yield None
            # this is a non-blocking read (ie, it will return if any data is available)
            try:
                if self.timeout:
                    if not self.buf.strip():
                        ready_to_read = select.select([sock], [], [], self.timeout)
                        if not ready_to_read[0] and time.time() - self.timer > self.timeout:
                            yield {"timeout":True}
                            continue
                self.buf += sock.recv(1024)
            except SSLError as e:
                if (not self.block or self.timeout) and (e.errno == 2):
                    # Apparently this means there was nothing in the socket buf
                    pass
                else:
                    raise TwitterHTTPError(e, self.uri, "json", self.arg_data)

def handle_stream_response(req, uri, arg_data, block=True, timeout=None):
    try:
        handle = urllib_request.urlopen(req,)
        return iter(TwitterJSONIter(handle, uri, arg_data, block, timeout=timeout,
            display_sizes=("delimited=length" in req.get_data().lower())))
    except urllib_error.HTTPError as e:
        raise TwitterHTTPError(e, uri, "json", arg_data)

class TwitterStreamCallWithTimeout(TwitterCall):
    def _handle_response(self, req, uri, arg_data, _timeout=None):
        return handle_stream_response(req, uri, arg_data, timeout=self.timeout)

class TwitterStreamCall(TwitterCall):
    def _handle_response(self, req, uri, arg_data, _timeout=None):
        return handle_stream_response(req, uri, arg_data)

class TwitterStreamCallNonBlocking(TwitterCall):
    def _handle_response(self, req, uri, arg_data, _timeout=None):
        return handle_stream_response(req, uri, arg_data, block=False)

class TwitterStream(TwitterStreamCall):
    """
    The TwitterStream object is an interface to the Twitter Stream API
    (stream.twitter.com). This can be used pretty much the same as the
    Twitter class except the result of calling a method will be an
    iterator that yields objects decoded from the stream. For
    example::

        twitter_stream = TwitterStream(auth=OAuth(...))
        iterator = twitter_stream.statuses.sample()

        for tweet in iterator:
            ...do something with this tweet...

    The iterator will yield tweets forever and ever (until the stream
    breaks at which point it raises a TwitterHTTPError.)

    The `block` parameter controls if the stream is blocking. Default
    is blocking (True). When set to False, the iterator will
    occasionally yield None when there is no available message.
    """
    def __init__(
        self, domain="stream.twitter.com", secure=True, auth=None,
        api_version='1.1', block=True, timeout=None):
        uriparts = ()
        uriparts += (str(api_version),)

        if block:
            if timeout:
                call_cls = TwitterStreamCallWithTimeout
            else:
                call_cls = TwitterStreamCall
        else:
            call_cls = TwitterStreamCallNonBlocking

        TwitterStreamCall.__init__(
            self, auth=auth, format="json", domain=domain,
            callable_cls=call_cls,
            secure=secure, uriparts=uriparts, timeout=timeout, gzip=False)
