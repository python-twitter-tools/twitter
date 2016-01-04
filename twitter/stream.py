# encoding: utf-8
from __future__ import unicode_literals

from .util import PY_3_OR_HIGHER

if PY_3_OR_HIGHER:
    import urllib.request as urllib_request
    import urllib.error as urllib_error
else:
    import urllib2 as urllib_request
    import urllib2 as urllib_error
import json
from ssl import SSLError
import socket
import codecs
import sys, select, time

from .api import TwitterCall, wrap_response, TwitterHTTPError

CRLF = b'\r\n'
MIN_SOCK_TIMEOUT = 0.0  # Apparenty select with zero wait is okay!
MAX_SOCK_TIMEOUT = 10.0
HEARTBEAT_TIMEOUT = 90.0

Timeout = {'timeout': True}
Hangup = {'hangup': True}
DecodeError = {'hangup': True, 'decode_error': True}
HeartbeatTimeout = {'hangup': True, 'heartbeat_timeout': True}


class HttpChunkDecoder(object):

    def __init__(self):
        self.buf = bytearray()
        self.munch_crlf = False

    def decode(self, data):  # -> (bytearray, end_of_stream, decode_error)
        chunks = []
        buf = self.buf
        munch_crlf = self.munch_crlf
        end_of_stream = False
        decode_error = False
        buf.extend(data)
        while True:
            if munch_crlf:
                # Dang, Twitter, you crazy. Twitter only sends a terminating
                # CRLF at the beginning of the *next* message.
                if len(buf) >= 2:
                    buf = buf[2:]
                    munch_crlf = False
                else:
                    break

            header_end_pos = buf.find(CRLF)
            if header_end_pos == -1:
                break

            header = buf[:header_end_pos]
            data_start_pos = header_end_pos + 2
            try:
                chunk_len = int(header.decode('ascii'), 16)
            except ValueError:
                decode_error = True
                break

            if chunk_len == 0:
                end_of_stream = True
                break

            data_end_pos = data_start_pos + chunk_len

            if len(buf) >= data_end_pos:
                chunks.append(buf[data_start_pos:data_end_pos])
                buf = buf[data_end_pos:]
                munch_crlf = True
            else:
                break
        self.buf = buf
        self.munch_crlf = munch_crlf
        return bytearray().join(chunks), end_of_stream, decode_error


class JsonDecoder(object):

    def __init__(self):
        self.buf = ""
        self.raw_decode = json.JSONDecoder().raw_decode

    def decode(self, data):
        chunks = []
        buf = self.buf + data
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


class SockReader(object):
    def __init__(self, sock, sock_timeout):
        self.sock = sock
        self.sock_timeout = sock_timeout

    def read(self):
        try:
            ready_to_read = select.select([self.sock], [], [], self.sock_timeout)[0]
            if ready_to_read:
                return self.sock.read()
        except SSLError as e:
            # Code 2 is error from a non-blocking read of an empty buffer.
            if e.errno != 2:
                raise
        return bytearray()


class TwitterJSONIter(object):

    def __init__(self, handle, uri, arg_data, block, timeout, heartbeat_timeout):
        self.handle = handle
        self.uri = uri
        self.arg_data = arg_data
        self.timeout_token = Timeout
        self.timeout = None
        self.heartbeat_timeout = HEARTBEAT_TIMEOUT
        if timeout and timeout > 0:
            self.timeout = float(timeout)
        elif not (block or timeout):
            self.timeout_token = None
            self.timeout = MIN_SOCK_TIMEOUT
        if heartbeat_timeout and heartbeat_timeout > 0:
            self.heartbeat_timeout = float(heartbeat_timeout)

    def __iter__(self):
        timeouts = [t for t in (self.timeout, self.heartbeat_timeout, MAX_SOCK_TIMEOUT)
                    if t is not None]
        sock_timeout = min(*timeouts)
        sock = self.handle.fp.raw._sock if PY_3_OR_HIGHER else self.handle.fp._sock.fp._sock
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        headers = self.handle.headers
        sock_reader = SockReader(sock, sock_timeout)
        chunk_decoder = HttpChunkDecoder()
        utf8_decoder = codecs.getincrementaldecoder("utf-8")()
        json_decoder = JsonDecoder()
        timer = Timer(self.timeout)
        heartbeat_timer = Timer(self.heartbeat_timeout)

        while True:
            # Decode all the things:
            try:
                data = sock_reader.read()
            except SSLError:
                yield Hangup
                break
            dechunked_data, end_of_stream, decode_error = chunk_decoder.decode(data)
            unicode_data = utf8_decoder.decode(dechunked_data)
            json_data = json_decoder.decode(unicode_data)

            # Yield data-like things:
            for json_obj in json_data:
                yield wrap_response(json_obj, headers)

            # Reset timers:
            if dechunked_data:
                heartbeat_timer.reset()
            if json_data:
                timer.reset()

            # Yield timeouts and special things:
            if end_of_stream:
                yield Hangup
                break
            if decode_error:
                yield DecodeError
                break
            if heartbeat_timer.expired():
                yield HeartbeatTimeout
                break
            if timer.expired():
                yield self.timeout_token


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
            # ...do something with this tweet...

    Per default the ``TwitterStream`` object uses
    [public streams](https://dev.twitter.com/docs/streaming-apis/streams/public).
    If you want to use one of the other
    [streaming APIs](https://dev.twitter.com/docs/streaming-apis), specify the URL
    manually:

    - [Public streams](https://dev.twitter.com/docs/streaming-apis/streams/public): stream.twitter.com
    - [User streams](https://dev.twitter.com/docs/streaming-apis/streams/user): userstream.twitter.com
    - [Site streams](https://dev.twitter.com/docs/streaming-apis/streams/site): sitestream.twitter.com

    Note that you require the proper
    [permissions](https://dev.twitter.com/docs/application-permission-model) to
    access these streams. E.g. for direct messages your
    [application](https://dev.twitter.com/apps) needs the "Read, Write & Direct
    Messages" permission.

    The following example demonstrates how to retrieve all new direct messages
    from the user stream::

        auth = OAuth(
            consumer_key='[your consumer key]',
            consumer_secret='[your consumer secret]',
            token='[your token]',
            token_secret='[your token secret]'
        )
        twitter_userstream = TwitterStream(auth=auth, domain='userstream.twitter.com')
        for msg in twitter_userstream.user():
            if 'direct_message' in msg:
                print msg['direct_message']['text']

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
