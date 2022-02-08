# encoding: utf-8

import json
import re
import unittest
try:
    from mock import patch
except ImportError:
    from unittest.mock import patch

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


class TestCmdLine(unittest.TestCase):

    status = {
        "created_at": "sun dec 20 18:33:30 +0000 2020",
        "user": {"screen_name": "myusername", "location": "Paris, France"},
        "text": "test &amp; test",
    }

    def test_replaceInStatus(self):
        status = "my&amp;status @twitter #tag"
        assert replaceInStatus(status) == "my&status @twitter #tag"

    @patch("twitter.cmdline.get_time_string", return_value="18:33:30 ")
    def test_StatusFormatter(self, mock_get_time_string):
        test_status = StatusFormatter()
        options = {"timestamp": True, "datestamp": False}
        assert test_status(self.status, options) == "18:33:30 @myusername test & test"

    def test_VerboseStatusFormatter(self):
        test_status = VerboseStatusFormatter()
        options = {"timestamp": True, "datestamp": False}
        assert (
            test_status(self.status, options)
            == "-- myusername (Paris, France) on sun dec 20 18:33:30 +0000 2020\ntest & test\n"
        )

    def test_JSONStatusFormatter(self):
        test_status = JSONStatusFormatter()
        options = {"timestamp": True, "datestamp": False}
        assert test_status(self.status, options) == json.dumps(
            {
                "created_at": "sun dec 20 18:33:30 +0000 2020",
                "user": {"screen_name": "myusername", "location": "Paris, France"},
                "text": "test & test",
            }
        )
