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

def recv_chunk(sock):  # -> bytearray:

    buf = sock.recv(10)  # Scan for an up to a 4GiB chunk size (0xffffffff).
    if buf:
        crlf = buf.find(b'\r\n')  # Find the HTTP chunk size.
        if crlf > 0:
            remaining = int(buf[:crlf], 16)  # Decode the chunk size.
            chunk = bytearray(remaining)  # Create the chunk buffer.

            start = crlf + 2  # Add in the length of the header's CRLF pair.
            end = len(buf) - start

            chunk[:end] = buf[start:]
            chunk[end:] = sock.recv(remaining - end)

            sock.recv(2)  # Read the trailing CRLF pair. Throw it away.

            return chunk
    return bytearray()

##  recv_chunk()


class TwitterJSONIter(object):

    def __init__(self, handle, uri, arg_data, block=True, timeout=None):
        self.handle = handle
        self.uri = uri
        self.arg_data = arg_data
        self.block = block
        self.timeout = timeout


    def __iter__(self):
        sock = self.handle.fp.raw._sock if sys.version_info >= (3, 0) else self.handle.fp._sock.fp._sock
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        if not self.block or self.timeout:
            sock.setblocking(False)
        buf = u''
        json_decoder = json.JSONDecoder()
        timer = time.time()
        while True:
            try:
                buf = buf.lstrip()
                res, ptr = json_decoder.raw_decode(buf)
                buf = buf[ptr:]
                yield wrap_response(res, self.handle.headers)
                timer = time.time()
                continue
            except ValueError as e:
                if self.block:
                    pass
                else:
                    yield None
            # this is a non-blocking read (ie, it will return if any data is available)
            try:
                if self.timeout:
                    ready_to_read = select.select([sock], [], [], self.timeout)
                    if ready_to_read[0]:
                        buf += recv_chunk(sock).decode('utf-8')
                        if time.time() - timer > self.timeout:
                            yield {"timeout": True}
                    else:
                        yield {"timeout": True}
                else:
                    buf += recv_chunk(sock).decode('utf-8')
            except SSLError as e:
                if (not self.block or self.timeout) and (e.errno == 2):
                    # Apparently this means there was nothing in the socket buf
                    pass
                else:
                    raise
            except urllib_error.HTTPError as e:
                raise TwitterHTTPError(e, self.uri, 'json', self.arg_data)

def handle_stream_response(req, uri, arg_data, block, timeout=None):
    handle = urllib_request.urlopen(req,)
    return iter(TwitterJSONIter(handle, uri, arg_data, block, timeout=timeout))

class TwitterStreamCallWithTimeout(TwitterCall):
    def _handle_response(self, req, uri, arg_data, _timeout=None):
        return handle_stream_response(req, uri, arg_data, block=True, timeout=self.timeout)

class TwitterStreamCall(TwitterCall):
    def _handle_response(self, req, uri, arg_data, _timeout=None):
        return handle_stream_response(req, uri, arg_data, block=True)

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
