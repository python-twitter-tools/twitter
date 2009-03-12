
from base64 import b64encode
from urllib import urlencode

import urllib2

from exceptions import Exception

from twitter.twitter_globals import POST_ACTIONS

def _py26OrGreater():
    import sys
    return sys.hexversion > 0x20600f0

if _py26OrGreater():
    import json
else:
    import simplejson as json

class TwitterError(Exception):
    """
    Exception thrown by the Twitter object when there is an
    error interacting with twitter.com.
    """
    pass

class TwitterCall(object):
    def __init__(
        self, username, password, format, domain, uri="", agent=None):
        self.username = username
        self.password = password
        self.format = format
        self.domain = domain
        self.uri = uri
        self.agent = agent
    def __getattr__(self, k):
        try:
            return object.__getattr__(self, k)
        except AttributeError:
            return TwitterCall(
                self.username, self.password, self.format, self.domain,
                self.uri + "/" + k, self.agent)
    def __call__(self, **kwargs):
        uri = self.uri
        method = "GET"
        for action in POST_ACTIONS:
            if self.uri.endswith(action):
                method = "POST"
                if (self.agent):
                    kwargs["source"] = self.agent
                break

        id = kwargs.pop('id', None)
        if id:
            uri += "/%s" %(id)

        argStr = ""
        argData = None
        encoded_kwargs = urlencode(kwargs.items())
        if (method == "GET"):
            if kwargs:
                argStr = "?%s" %(encoded_kwargs)
        else:
            argData = encoded_kwargs

        headers = {}
        if (self.agent):
            headers["X-Twitter-Client"] = self.agent
        if (self.username):
            headers["Authorization"] = "Basic " + b64encode("%s:%s" %(
                self.username, self.password))

        req = urllib2.Request(
                "http://%s/%s.%s%s" %(self.domain, uri, self.format, argStr),
                argData, headers
            )
        try:
            handle = urllib2.urlopen(req)
            if "json" == self.format:
                return json.loads(handle.read())
            else:
                return handle.read()
        except urllib2.HTTPError, e:
            if (e.code == 304):
                return []
            else:
                raise TwitterError(
                    "Twitter sent status %i for URL: %s.%s using parameters: (%s)\ndetails: %s" %(
                        e.code, uri, self.format, encoded_kwargs, e.fp.read()))

class Twitter(TwitterCall):
    """
    The minimalist yet fully featured Twitter API class.

    Get RESTful data by accessing members of this class. The result
    is decoded python objects (lists and dicts).

    The Twitter API is documented here:

      http://apiwiki.twitter.com/
      http://groups.google.com/group/twitter-development-talk/web/api-documentation

    Examples::

      twitter = Twitter("hello@foo.com", "password123")

      # Get the public timeline
      twitter.statuses.public_timeline()

      # Get a particular friend's timeline
      twitter.statuses.friends_timeline(id="billybob")

      # Also supported (but totally weird)
      twitter.statuses.friends_timeline.billybob()

      # Send a direct message
      twitter.direct_messages.new(
          user="billybob",
          text="I think yer swell!")

    Searching Twitter::

      twitter_search = Twitter(domain="search.twitter.com")

      # Find the latest search trends
      twitter_search.trends()

      # Search for the latest News on #gaza
      twitter_search.search(q="#gaza")

    Using the data returned::

      Twitter API calls return decoded JSON. This is converted into
      a bunch of Python lists, dicts, ints, and strings. For example,

      x = twitter.statuses.public_timeline()

      # The first 'tweet' in the timeline
      x[0]

      # The screen name of the user who wrote the first 'tweet'
      x[0]['user']['screen_name']

    Getting raw XML data::

      If you prefer to get your Twitter data in XML format, pass
      format="xml" to the Twitter object when you instantiate it:

      twitter = Twitter(format="xml")

      The output will not be parsed in any way. It will be a raw string
      of XML.
    """
    def __init__(
        self, email=None, password=None, format="json", domain="twitter.com",
        agent=None):
        """
        Create a new twitter API connector using the specified
        credentials (email and password). Format specifies the output
        format ("json" (default) or "xml").
        """
        if (format not in ("json", "xml")):
            raise TwitterError("Unknown data format '%s'" %(format))
        TwitterCall.__init__(self, email, password, format, domain, "", agent)

__all__ = ["Twitter", "TwitterError"]
