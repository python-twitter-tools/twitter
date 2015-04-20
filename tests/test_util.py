# encoding: utf-8
from __future__ import unicode_literals

from collections import namedtuple
import contextlib
import functools
import socket
import threading
from twitter.util import find_links, follow_redirects, expand_line, parse_host_list

try:
    import http.server as BaseHTTPServer
    import socketserver as SocketServer
except ImportError:
    import BaseHTTPServer
    import SocketServer


def test_find_links():
    assert find_links("nix") == ("nix", [])
    assert find_links("http://abc") == ("%s", ["http://abc"])
    assert find_links("t http://abc") == ("t %s", ["http://abc"])
    assert find_links("http://abc t") == ("%s t", ["http://abc"])
    assert find_links("1 http://a 2 http://b 3") == ("1 %s 2 %s 3",
        ["http://a", "http://b"])
    assert find_links("%") == ("%%", [])
    assert find_links("(http://abc)") == ("(%s)", ["http://abc"])


Response = namedtuple('Response', 'path code headers')

@contextlib.contextmanager
def start_server(*resp):
    """HTTP server replying with the given responses to the expected
    requests."""
    def url(port, path):
        return 'http://%s:%s%s' % (socket.gethostname().lower(), port, path)

    responses = list(reversed(resp))

    class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
        def do_HEAD(self):
            response = responses.pop()
            assert response.path == self.path
            self.send_response(response.code)
            for header, value in list(response.headers.items()):
                self.send_header(header, value)
            self.end_headers()

    httpd = SocketServer.TCPServer(("", 0), MyHandler)
    t = threading.Thread(target=httpd.serve_forever)
    t.setDaemon(True)
    t.start()
    port = httpd.server_address[1]
    yield functools.partial(url, port)
    httpd.shutdown()

def test_follow_redirects_direct_link():
    link = "/resource"
    with start_server(Response(link, 200, {})) as url:
        assert url(link) == follow_redirects(url(link))

def test_follow_redirects_redirected_link():
    redirected = "/redirected"
    link = "/resource"
    with start_server(
        Response(link, 301, {"Location": redirected}),
        Response(redirected, 200, {})) as url:
        assert url(redirected) == follow_redirects(url(link))

def test_follow_redirects_unavailable():
    link = "/resource"
    with start_server(Response(link, 404, {})) as url:
        assert url(link) == follow_redirects(url(link))

def test_follow_redirects_link_to_last_available():
    unavailable = "/unavailable"
    link = "/resource"
    with start_server(
        Response(link, 301, {"Location": unavailable}),
        Response(unavailable, 404, {})) as url:
        assert url(unavailable) == follow_redirects(url(link))


def test_follow_redirects_no_where():
    link = "http://links.nowhere/"
    assert link == follow_redirects(link)

def test_follow_redirects_link_to_nowhere():
    unavailable = "http://links.nowhere/"
    link = "/resource"
    with start_server(
        Response(link, 301, {"Location": unavailable})) as url:
        assert unavailable == follow_redirects(url(link))

def test_follow_redirects_filtered_by_site():
    link = "/resource"
    with start_server() as url:
        assert url(link) == follow_redirects(url(link), ["other_host"])


def test_follow_redirects_filtered_by_site_after_redirect():
    link = "/resource"
    redirected = "/redirected"
    filtered = "http://dont-follow/"
    with start_server(
        Response(link, 301, {"Location": redirected}),
        Response(redirected, 301, {"Location": filtered})) as url:
        hosts = [socket.gethostname().lower()]
        assert filtered == follow_redirects(url(link), hosts)

def test_follow_redirects_filtered_by_site_allowed():
    redirected = "/redirected"
    link = "/resource"
    with start_server(
        Response(link, 301, {"Location": redirected}),
        Response(redirected, 200, {})) as url:
        hosts = [socket.gethostname().lower()]
        assert url(redirected) == follow_redirects(url(link), hosts)

def test_expand_line():
    redirected = "/redirected"
    link = "/resource"
    with start_server(
        Response(link, 301, {"Location": redirected}),
        Response(redirected, 200, {})) as url:
        fmt = "before %s after"
        line = fmt % url(link)
        expected = fmt % url(redirected)
        assert expected == expand_line(line, None)

def test_parse_host_config():
    assert set() == parse_host_list("")
    assert set("h") == parse_host_list("h")
    assert set(["1", "2"]) == parse_host_list("1,2")
    assert set(["1", "2"]) == parse_host_list(" 1 , 2 ")

