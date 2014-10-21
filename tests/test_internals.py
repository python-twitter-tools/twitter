# encoding: utf-8
from __future__ import unicode_literals

from twitter.api import method_for_uri, build_uri

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
