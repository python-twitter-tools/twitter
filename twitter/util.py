"""
Internal utility functions.

`htmlentitydecode` came from here:
    http://wiki.python.org/moin/EscapingHtml
"""

from __future__ import print_function

import contextlib
import re
import sys
import textwrap
import time
import socket

PY_3_OR_HIGHER = sys.version_info >= (3, 0)

try:
    from html.entities import name2codepoint
    unichr = chr
    import urllib.request as urllib2
    import urllib.parse as urlparse
except ImportError:
    from htmlentitydefs import name2codepoint
    import urllib2
    import urlparse

def htmlentitydecode(s):
    return re.sub(
        '&(%s);' % '|'.join(name2codepoint),
        lambda m: unichr(name2codepoint[m.group(1)]), s)

def smrt_input(globals_, locals_, ps1=">>> ", ps2="... "):
    inputs = []
    while True:
        if inputs:
            prompt = ps2
        else:
            prompt = ps1
        inputs.append(input(prompt))
        try:
            ret = eval('\n'.join(inputs), globals_, locals_)
            if ret:
                print(str(ret))
            return
        except SyntaxError:
            pass

def printNicely(string):
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout.buffer.write(string.encode('utf8'))
        print()
        sys.stdout.buffer.flush()
        sys.stdout.flush()
    else:
        print(string.encode('utf8'))

def actually_bytes(stringy):
    if PY_3_OR_HIGHER:
        if type(stringy) == bytes:
            pass
        elif type(stringy) != str:
            stringy = str(stringy)
        if type(stringy) == str:
            stringy = stringy.encode("utf-8")
    else:
        if type(stringy) == str:
            pass
        elif type(stringy) != unicode:
            stringy = str(stringy)
        if type(stringy) == unicode:
            stringy = stringy.encode("utf-8")
    return stringy

def err(msg=""):
    print(msg, file=sys.stderr)


class Fail(object):
    """A class to count fails during a repetitive task.

    Args:
        maximum: An integer for the maximum of fails to allow.
        exit: An integer for the exit code when maximum of fail is reached.

    Methods:
        count: Count a fail, exit when maximum of fails is reached.
        wait: Same as count but also sleep for a given time in seconds.
    """
    def __init__(self, maximum=10, exit=1):
        self.i = maximum
        self.exit = exit

    def count(self):
        self.i -= 1
        if self.i == 0:
            err("Too many consecutive fails, exiting.")
            raise SystemExit(self.exit)

    def wait(self, delay=0):
        self.count()
        if delay > 0:
            time.sleep(delay)


def find_links(line):
    """Find all links in the given line. The function returns a sprintf style
    format string (with %s placeholders for the links) and a list of urls."""
    l = line.replace("%", "%%")
    regex = "(https?://[^ )]+)"
    return (
        re.sub(regex, "%s", l),
        [m.group(1) for m in re.finditer(regex, l)])

def follow_redirects(link, sites= None):
    """Follow directs for the link as long as the redirects are on the given
    sites and return the resolved link."""
    def follow(url):
        return sites == None or urlparse.urlparse(url).hostname in sites

    class RedirectHandler(urllib2.HTTPRedirectHandler):
        def __init__(self):
            self.last_url = None
        def redirect_request(self, req, fp, code, msg, hdrs, newurl):
            self.last_url = newurl
            if not follow(newurl):
                return None
            r = urllib2.HTTPRedirectHandler.redirect_request(
                self, req, fp, code, msg, hdrs, newurl)
            r.get_method = lambda : 'HEAD'
            return r

    if not follow(link):
        return link
    redirect_handler = RedirectHandler()
    opener = urllib2.build_opener(redirect_handler)
    req = urllib2.Request(link)
    req.get_method = lambda : 'HEAD'
    try:
        with contextlib.closing(opener.open(req,timeout=1)) as site:
            return site.url
    except:
        return redirect_handler.last_url if redirect_handler.last_url else link

def expand_line(line, sites):
    """Expand the links in the line for the given sites."""
    try:
        l = line.strip()
        msg_format, links = find_links(l)
        args = tuple(follow_redirects(l, sites) for l in links)
        line = msg_format % args
    except Exception as e:
        try:
            err("expanding line %s failed due to %s" % (line, unicode(e)))
        except:
            pass
    return line

def parse_host_list(list_of_hosts):
    """Parse the comma separated list of hosts."""
    p = {
        m.group(1) for m in re.finditer(r"\s*([^,\s]+)\s*,?\s*", list_of_hosts)}
    return p


def align_text(text, left_margin=17, max_width=160):
    lines = []
    for line in text.split('\n'):
        temp_lines = textwrap.wrap(line, max_width - left_margin)
        temp_lines = [(' ' * left_margin + line) for line in temp_lines]
        lines.append('\n'.join(temp_lines))
    ret = '\n'.join(lines)
    return ret.lstrip()


__all__ = ["htmlentitydecode", "smrt_input"]
