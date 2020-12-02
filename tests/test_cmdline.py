# encoding: utf-8

import json
import re

try:
    import HTMLParser
except ImportError:
    import html.parser as HTMLParser

from twitter.cmdline import (
    replaceInStatus,
    StatusFormatter,
    VerboseStatusFormatter,
    JSONStatusFormatter,
)


status = {
    "created_at": "sun dec 20 18:33:30 +0000 2020",
    "user": {"screen_name": "myusername", "location": "Paris"},
    "text": "test &amp; test",
}


def test_replaceInStatus():
    status = "my&amp;status @twitter #tag"
    assert replaceInStatus(status) == "my&status @twitter #tag"


def test_StatusFormatter():
    test_status = StatusFormatter()
    options = {"timestamp": True, "datestamp": False}
    assert test_status(status, options) == "20:33:30 @myusername test & test"


def test_VerboseStatusFormatter():
    test_status = VerboseStatusFormatter()
    options = {"timestamp": True, "datestamp": False}
    assert (
        test_status(status, options)
        == "-- myusername (Paris) on sun dec 20 18:33:30 +0000 2020\ntest & test\n"
    )


def test_JSONStatusFormatter():
    test_status = JSONStatusFormatter()
    options = {"timestamp": True, "datestamp": False}
    assert test_status(status, options) == json.dumps(
        {
            "created_at": "sun dec 20 18:33:30 +0000 2020",
            "user": {"screen_name": "myusername", "location": "Paris"},
            "text": "test & test",
        }
    )
