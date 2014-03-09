try:
    import urllib.request as urllib_request
    import urllib.error as urllib_error
except ImportError:
    import urllib2 as urllib_request
    import urllib2 as urllib_error
import io
import json
from ssl import SSLError
import socket
import sys, select, time

from .api import TwitterCall, wrap_response, TwitterHTTPError

PY_3_OR_HIGHER = sys.version_info >= (3, 0)

CRLF = b'\r\n'

Timeout = {'timeout': True}
Hangup = {'hangup': True}
HeartbeatTimeout = {'heartbeat_timeout': True, 'hangup': True}

class ChunkDecodeError(Exception):
    pass

class EndOfStream(Exception):
    pass

range = range if PY_3_OR_HIGHER else xrange

class SocketShim(io.IOBase):
    """
    Adapts a raw socket to fit the IO protocol.
    """
    def __init__(self, sock):
        self.sock = sock
    def readable(self):
        return True
    def read(self, size):
        return self.sock.read(size)
    def readinto(self, buf):
        while True:
            try:
                return self.sock.recv_into(buf)
            except SSLError as e:
                # Code 2 is error from a non-blocking read of an empty buffer.
                if e.errno != 2:
                    raise

def recv_chunk(reader): # -> bytearray:
    for headerlen in range(12):
        header = reader.peek(headerlen)[:headerlen]
        if header.endswith(CRLF):
            break
    else:
        raise ChunkDecodeError()

    size = int(header, 16) # Decode the chunk size
    reader.read(headerlen) # Ditch the header

    if size == 0:
        raise EndOfStream()

    chunk = bytearray()
    while len(chunk) < size:
        remainder = size - len(chunk)
        chunk.extend(reader.read(remainder))

    reader.read(2) # Ditch remaining CRLF

    return chunk


class Timer(object):
    def __init__(self, timeout):
        # If timeout is None, we never expire.
        self.timeout = timeout
        self.reset()

    def reset(self):
        self.time = time.time()

    def expired(self):
        """
        If expired, reset the timer and return True.
        """
        if self.timeout is None:
            return False
        elif time.time() - self.time > self.timeout:
            self.reset()
            return True
        return False


class TwitterJSONIter(object):

    def __init__(self, handle, uri, arg_data, block, timeout, heartbeat_timeout):
        self.handle = handle
        self.uri = uri
        self.arg_data = arg_data
        self.block = block
        self.timeout = float(timeout) if timeout else None
        self.heartbeat_timeout = float(heartbeat_timeout) if heartbeat_timeout else None


    def __iter__(self):
        actually_block = self.block and not self.timeout
        sock_timeout = min(self.timeout or 1000000, self.heartbeat_timeout)
        sock = self.handle.fp.raw._sock if PY_3_OR_HIGHER else self.handle.fp._sock.fp._sock
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        sock.setblocking(actually_block)
        reader = io.BufferedReader(SocketShim(sock))
        buf = ''
        raw_decode = json.JSONDecoder().raw_decode
        timer = Timer(self.timeout)
        heartbeat_timer = Timer(self.heartbeat_timeout)
        while True:
            buf = buf.lstrip() # Remove any keep-alive delimiters
            try:
                res, ptr = raw_decode(buf)
                buf = buf[ptr:]
            except ValueError:
                if not self.block and not self.timeout:
                    yield None
            else:
                yield wrap_response(res, self.handle.headers)
                timer.reset()
                heartbeat_timer.reset()
                continue

            if heartbeat_timer.expired():
                yield HeartbeatTimeout
                break
            if timer.expired():
                yield Timeout

            try:
                ready_to_read = select.select([sock], [], [], sock_timeout)[0]
                if not ready_to_read:
                    continue
                received = recv_chunk(reader)
                buf += received.decode('utf-8')
                if received:
                    heartbeat_timer.reset()
            except (ChunkDecodeError, EndOfStream):
                yield Hangup
                break

def handle_stream_response(req, uri, arg_data, block, timeout, heartbeat_timeout):
    try:
        handle = urllib_request.urlopen(req,)
    except urllib_error.HTTPError as e:
        raise TwitterHTTPError(e, uri, 'json', arg_data)
    return iter(TwitterJSONIter(handle, uri, arg_data, block, timeout, heartbeat_timeout))

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

    Similarly, if the stream does not produce heartbeats for more than
    90 seconds, the iterator yields `{'hangup': True,
    'heartbeat_timeout': True}`, and raises `StopIteration` if
    iterated again.

    The `timeout` parameter controls the maximum time between
    yields. If it is nonzero, then the iterator will yield either
    stream data or `{'timeout': True}` within the timeout period. This
    is useful if you want your program to do other stuff in between
    waiting for tweets.

    The `block` parameter sets the stream to be fully non-blocking. In
    this mode, the iterator always yields immediately. It returns
    stream data, or `None`. Note that `timeout` supercedes this
    argument, so it should also be set `None` to use this mode.
    """
    def __init__(self, domain="stream.twitter.com", secure=True, auth=None,
                 api_version='1.1', block=True, timeout=None,
                 heartbeat_timeout=90.0):
        uriparts = (str(api_version),)

        class TwitterStreamCall(TwitterCall):
            def _handle_response(self, req, uri, arg_data, _timeout=None):
                return handle_stream_response(
                    req, uri, arg_data, block,
                    _timeout or timeout, heartbeat_timeout)

        TwitterCall.__init__(
            self, auth=auth, format="json", domain=domain,
            callable_cls=TwitterStreamCall,
            secure=secure, uriparts=uriparts, timeout=timeout, gzip=False)
