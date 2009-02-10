from urllib import urlencode

from httplib2 import Http

from exceptions import Exception

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
    def __init__(self, http, format, domain, uri=""):
        self.http = http
        self.format = format
        self.uri = uri
    def __getattr__(self, k):
        try:
            return object.__getattr__(self, k)
        except AttributeError:
            return TwitterCall(self.http, self.format, self.uri + "/" + k)
    def __call__(self, **kwargs):
        method = (self.uri.endswith('new')
                  or self.uri.endswith('update')
                  or self.uri.endswith('create')
                  or self.uri.endswith('destroy')) and "POST" or "GET"

        encoded_kwargs = urlencode(kwargs.items())
        argStr = ""
        if encoded_kwargs and (method == "GET"):
            argStr = "?" + encoded_kwargs

        kwargs = {
            "uri": "%s.%s%s" % (self.uri,self.format,argStr),
            "method": method
        }

        if method == "POST":
            kwargs["headers"] = {}
            kwargs["headers"]["Content-type"] = "application/x-www-form-urlencoded"
            kwargs["headers"]["Content-length"] = len(encoded_kwargs)
            kwargs["body"] = encoded_kwargs

        try:
            response, content = self.http.request(**kwargs)
            if (response.status == 304):
                return []
            elif (response.status != 200):
                raise TwitterError("Twitter sent status %i: %s" % (response.status,content))
            if "json" == self.format:
                return json.loads(content)
            else:
                return content
        finally:
            pass

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
      twitter_search(q="#gaza")
        
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
    def __init__(self, username=None, password=None, format="json", domain="twitter.com"):
        """
        Create a new twitter API connector using the specified
        credentials (email and password). Format specifies the output
        format ("json" (default) or "xml").
        """
        if (format not in ("json", "xml")):
            raise TwitterError("Unknown data format '%s'" % (format))

        http = Http()
        http.add_credentials(username, password, domain)
        TwitterCall.__init__(self, http, format, "http://%s" % (domain))

__all__ = ["Twitter", "TwitterError"]
