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

PY_27_OR_HIGHER = sys.version_info >= (2, 7)
PY_3_OR_HIGHER = sys.version_info >= (3, 0)

Timeout = {'timeout': True}
Hangup = {'hangup': True}


def recv_chunk(sock): # -> bytearray:

    header = sock.recv(8)  # Scan for an up to 16MiB chunk size (0xffffff).
    crlf = header.find(b'\r\n')  # Find the HTTP chunk size.

    if crlf > 0:  # If there is a length, then process it

        size = int(header[:crlf], 16)  # Decode the chunk size. Rarely exceeds 8KiB.
        chunk = bytearray(size)
        start = crlf + 2  # Add in the length of the header's CRLF pair.

        if size <= 3:  # E.g. an HTTP chunk with just a keep-alive delimiter or end of stream (0).
            chunk[:size] = header[start:start + size]
        # There are several edge cases (size == [4-6]) as the chunk size exceeds the length
        # of the initial read of 8 bytes. With Twitter, these do not, in practice, occur. The
        # shortest JSON message starts with '{"limit":{'. Hence, it exceeds in size the edge cases
        # and eliminates the need to address them.
        else:  # There is more to read in the chunk.
            end = len(header) - start
            chunk[:end] = header[start:]
            if PY_27_OR_HIGHER:  # When possible, use less memory by reading directly into the buffer.
                buffer = memoryview(chunk)[end:]  # Create a view into the bytearray to hold the rest of the chunk.
                sock.recv_into(buffer)
            else:  # less efficient for python2.6 compatibility
                chunk[end:] = sock.recv(max(0, size - end))
            sock.recv(2)  # Read the trailing CRLF pair. Throw it away.

        return chunk

    return bytearray()


class Timer(object):
    def __init__(self, timeout):
        # If timeout is None, we always expire.
        self.timeout = timeout
        self.reset()

    def reset(self):
        self.time = time.time()

    def expired(self):
        """
        If expired, reset the timer and return True.
        """
        if self.timeout is None:
            return True
        elif time.time() - self.time > self.timeout:
            self.reset()
            return True
        return False


class TwitterJSONIter(object):

    def __init__(self, handle, uri, arg_data, block=True, timeout=None):
        self.handle = handle
        self.uri = uri
        self.arg_data = arg_data
        self.block = block
        self.timeout = timeout


    def __iter__(self):
        actually_blocking = self.block and not self.timeout
        sock = self.handle.fp.raw._sock if PY_3_OR_HIGHER else self.handle.fp._sock.fp._sock
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        sock.setblocking(actually_blocking)
        buf = ''
        json_decoder = json.JSONDecoder()
        timer = Timer(self.timeout)
        timeout_token = Timeout if self.timeout else None
        while True:
            buf = buf.lstrip() # Remove any keep-alive delimiters to detect hangups.
            try:
                res, ptr = json_decoder.raw_decode(buf)
                buf = buf[ptr:]
            except ValueError:
                pass
            else:
                yield wrap_response(res, self.handle.headers)
                timer.reset()
                continue
            try:
                if self.timeout and not buf:  # This is a non-blocking read.
                    ready_to_read = select.select([sock], [], [], self.timeout)[0]
                    if not ready_to_read and timer.expired():
                        yield timeout_token
                        continue
                buf += recv_chunk(sock).decode('utf-8')
                if not buf:
                    yield Hangup
                    break
            except SSLError as e:
                # Error from a non-blocking read of an empty buffer.
                if not actually_blocking and (e.errno == 2):
                    if timer.expired():
                        yield timeout_token
                else: raise

def handle_stream_response(req, uri, arg_data, block, timeout=None):
    try:
        handle = urllib_request.urlopen(req,)
    except urllib_error.HTTPError as e:
        raise TwitterHTTPError(e, uri, 'json', arg_data)
    return iter(TwitterJSONIter(handle, uri, arg_data, block, timeout=timeout))

class TwitterStream(TwitterCall):
    """
    The TwitterStream object is an interface to the Twitter Stream
    API. This can be used pretty much the same as the Twitter class
    except the result of calling a method will be an iterator that
    yields objects decoded from the stream. For example::

        twitter_stream = TwitterStream(auth=OAuth(...))
        iterator = twitter_stream.statuses.sample()

        for tweet in iterator:
            ...do something with this tweet...

    The iterator will yield until the TCP connection breaks. When the
    connection breaks, the iterator yields `{'hangup': True}`, and
    raises `StopIteration` if iterated again.

    The `timeout` parameter controls the maximum time between
    yields. If it is nonzero, then the iterator will yield either
    stream data or `{'timeout': True}`. This is useful if you want
    your program to do other stuff in between waiting for tweets.

    The `block` parameter sets the stream to be non-blocking. In this
    mode, the iterator always yields immediately. It returns stream
    data, or `None`. Note that `timeout` supercedes this argument, so
    it should also be set `None` to use this mode.
    """
    def __init__(
        self, domain="stream.twitter.com", secure=True, auth=None,
        api_version='1.1', block=True, timeout=None):
        uriparts = (str(api_version),)
        timeout = float(timeout) if timeout else None

        class TwitterStreamCall(TwitterCall):
            def _handle_response(self, req, uri, arg_data, _timeout=None):
                return handle_stream_response(
                    req, uri, arg_data, block=block, timeout=_timeout or timeout)

        TwitterCall.__init__(
            self, auth=auth, format="json", domain=domain,
            callable_cls=TwitterStreamCall,
            secure=secure, uriparts=uriparts, timeout=timeout, gzip=False)
