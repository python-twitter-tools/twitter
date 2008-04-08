
from base64 import b64encode
from urllib import urlencode

import httplib

from exceptions import Exception

class TwitterError(Exception):
    pass

class TwitterCall(object):
    def __init__(self, username, password, format, uri=""):
        self.username = username
        self.password = password
        self.format = format
        self.uri = uri
    def __getattr__(self, k):
        try:
            return object.__getattr__(self, k)
        except AttributeError:
            return TwitterCall(
                self.username, self.password, self.format, 
                self.uri + "/" + k)
    def __call__(self, **kwargs):
        method = "GET"
        if self.uri.endswith('new') or self.uri.endswith('update'):
            method = "POST"
        argStr = ""
        if kwargs:
            argStr = "?" + urlencode(kwargs.items())
        c = httplib.HTTPConnection("twitter.com")
        try:
            c.putrequest(method, "/%s.%s%s" %(
                self.uri, self.format, argStr))
            if (self.username):
                c.putheader(
                    "Authorization", "Basic " + b64encode("%s:%s" %(
                        self.username, self.password)))
            if (method == "POST"):
                # TODO specify charset
                pass
            c.endheaders()
            r = c.getresponse()
            if (r.status == 304):
                return []
            elif (r.status != 200):
                raise TwitterError("Twitter sent status %i: %s" %(
                    r.status, r.read()))
            if ("json" == self.format):
                import simplejson
                return simplejson.loads(r.read())
            else:
                return r.read()
        finally:
            c.close()

class Twitter(TwitterCall):
    """
    The minimalist yet fully featured Twitter API class.
    
    Get RESTful data by accessing members of this class. The result
    is decoded python objects (lists and dicts).

    The Twitter API is documented here:
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
    def __init__(self, email=None, password=None, format="json"):
        """
        Create a new twitter API connector using the specified
        credentials (email and password). Format specifies the output
        format ("json" (default) or "xml").
        """
        if (format not in ("json", "xml")):
            raise TwitterError("Unknown data format '%s'" %(format))
        if (format == "json"):
            try:
                import simplejson
            except ImportError:
                raise TwitterError(
                    "format not available: simplejson is not installed")
        TwitterCall.__init__(self, email, password, format)

__all__ = ["Twitter"]
