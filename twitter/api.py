
from base64 import b64encode
from urllib import urlencode

import httplib
import simplejson

from exceptions import Exception

class TwitterError(Exception):
    pass

class TwitterCall(object):
    def __init__(self, username=None, password=None, uri=""):
        self.username = username
        self.password = password
        self.uri = uri
    def __getattr__(self, k):
        try:
            return object.__getattr__(self, k)
        except AttributeError:
            return TwitterCall(
                self.username, self.password, self.uri + "/" + k)
    def __call__(self, **kwargs):
        method = "GET"
        if self.uri.endswith('new') or self.uri.endswith('update'):
            method = "POST"
        argStr = ""
        if kwargs:
            argStr = "?" + urlencode(kwargs.items())
        c = httplib.HTTPConnection("twitter.com")
        try:
            c.putrequest(method, "/%s.json%s" %(self.uri, argStr))
            if (self.username):
                c.putheader("Authorization", "Basic " 
                            + b64encode("%s:%s" %(
                                self.username, self.password)))
            c.endheaders()
            r = c.getresponse()
            if (r.status == 304):
                return []
            elif (r.status != 200):
                raise TwitterError("Twitter sent status %i: %s" %(
                    r.status, r.read()))
            return simplejson.loads(r.read())
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
      
    """
    def __init__(self, email=None, password=None):
        """
        Create a new twitter API connector using the specified
        credentials (email and password).
        """
        TwitterCall.__init__(self, email, password)

__all__ = ["Twitter"]
