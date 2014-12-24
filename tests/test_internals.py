# encoding: utf-8
from __future__ import unicode_literals

from twitter.api import method_for_uri, build_uri
from twitter.util import PY_3_OR_HIGHER, actually_bytes

def test_method_for_uri__lookup():
    assert "POST" == method_for_uri("/1.1/users/lookup")
    assert "POST" == method_for_uri("/1.1/statuses/lookup")
    assert "POST" == method_for_uri("/1.1/users/lookup/12345")
    assert "GET" == method_for_uri("/1.1/friendships/lookup")

def test_build_uri():
    uri = build_uri(["1.1", "foo", "bar"], {})
    assert uri == "1.1/foo/bar"

    # Interpolation works
    uri = build_uri(["1.1", "_foo", "bar"], {"_foo": "asdf"})
    assert uri == "1.1/asdf/bar"

    # But only for strings beginning with _.
    uri = build_uri(["1.1", "foo", "bar"], {"foo": "asdf"})
    assert uri == "1.1/foo/bar"

def test_actually_bytes():
    out_type = str
    if PY_3_OR_HIGHER:
        out_type = bytes
    for inp in [b"asdf", "asdf", "asdfüü", 1234]:
        assert type(actually_bytes(inp)) == out_type
