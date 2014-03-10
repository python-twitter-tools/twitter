import sys
PY_3_OR_HIGHER = sys.version_info >= (3, 0)

if PY_3_OR_HIGHER:
    import urllib.request as urllib_request
    import urllib.error as urllib_error
else:
    import urllib2 as urllib_request
    import urllib2 as urllib_error
import json
from ssl import SSLError
import socket
import io
import codecs
import sys, select, time

from .api import TwitterCall, wrap_response, TwitterHTTPError

CRLF = b'\r\n'

Timeout = {'timeout': True}
Hangup = {'hangup': True}
HeartbeatTimeout = {'heartbeat_timeout': True, 'hangup': True}

class ChunkDecodeError(Exception):
    pass

class EndOfStream(Exception):
    pass

range = range if PY_3_OR_HIGHER else xrange


class HttpDeChunker(object):

    def __init__(self):
        self.buf = bytearray()

    def extend(self, data):
        self.buf.extend(data)

    def read_chunks(self):  # -> [bytearray]
        chunks = []
        buf = self.buf
        while True:
            header_end_pos = buf.find(CRLF)
            if header_end_pos == -1:
                break

            header = buf[:header_end_pos]
            data_start_pos = header_end_pos + 2
            try:
                chunk_len = int(header.decode('ascii'), 16)
            except ValueError:
                raise ChunkDecodeError()

            if chunk_len == 0:
                raise EndOfStream()

            data_end_pos = data_start_pos + chunk_len

            if len(buf) > data_end_pos + 2:
                chunks.append(buf[data_start_pos:data_end_pos])
                buf = buf[data_end_pos + 2:]
            else:
                break
        self.buf = buf
        return chunks


class JsonDeChunker(object):

    def __init__(self):
        self.buf = u""
        self.raw_decode = json.JSONDecoder().raw_decode

    def extend(self, data):
        self.buf += data

    def read_json_chunks(self):
        chunks = []
        buf = self.buf
        while True:
            try:
                buf = buf.lstrip()
                res, ptr = self.raw_decode(buf)
                buf = buf[ptr:]
                chunks.append(res)
            except ValueError:
                break
        self.buf = buf
        return chunks


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
        headers = self.handle.headers
        dechunker = HttpDeChunker()
        utf8decoder = codecs.getincrementaldecoder("utf-8")()
        json_dechunker = JsonDeChunker()
        timer = Timer(self.timeout)
        heartbeat_timer = Timer(self.heartbeat_timeout)
        while True:
            json_chunks = json_dechunker.read_json_chunks()
            for json in json_chunks:
                yield wrap_response(json, headers)
            if json_chunks:
                timer.reset()
                heartbeat_timer.reset()

            if not self.block and not self.timeout:
                yield None
            if heartbeat_timer.expired():
                yield HeartbeatTimeout
                break
            if timer.expired():
                yield Timeout

            try:
                ready_to_read = select.select([sock], [], [], sock_timeout)[0]
                if not ready_to_read:
                    continue
                data = sock.read()
            except SSLError as e:
                # Code 2 is error from a non-blocking read of an empty buffer.
                if e.errno != 2:
                    raise
                continue

            dechunker.extend(data)

            try:
                chunks = dechunker.read_chunks()
            except (ChunkDecodeError, EndOfStream):
                yield Hangup
                break

            for chunk in chunks:
                if chunk:
                    json_dechunker.extend(utf8decoder.decode(chunk))
            if chunks:
                heartbeat_timer.reset()

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
