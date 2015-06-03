Python Twitter Tools
====================

[![Build Status](https://travis-ci.org/sixohsix/twitter.svg)](https://travis-ci.org/sixohsix/twitter) [![Coverage Status](https://coveralls.io/repos/sixohsix/twitter/badge.png?branch=master)](https://coveralls.io/r/sixohsix/twitter?branch=master)

The Minimalist Twitter API for Python is a Python API for Twitter,
everyone's favorite Web 2.0 Facebook-style status updater for people
on the go.

Also included is a twitter command-line tool for getting your friends'
tweets and setting your own tweet from the safety and security of your
favorite shell and an IRC bot that can announce Twitter updates to an
IRC channel.

For more information, after installing the `twitter` package:

 * import the `twitter` package and run help() on it
 * run `twitter -h` for command-line tool help


twitter - The Command-Line Tool
-------------------------------

The command-line tool lets you do some awesome things:

 * view your tweets, recent replies, and tweets in lists
 * view the public timeline
 * follow and unfollow (leave) friends
 * various output formats for tweet information

The bottom line: type `twitter`, receive tweets.



twitterbot - The IRC Bot
------------------------

The IRC bot is associated with a twitter account (either your own account or an
account you create for the bot). The bot announces all tweets from friends
it is following. It can be made to follow or leave friends through IRC /msg
commands.


twitter-log
-----------

`twitter-log` is a simple command-line tool that dumps all public
tweets from a given user in a simple text format. It is useful to get
a complete offsite backup of all your tweets. Run `twitter-log` and
read the instructions.

twitter-archiver and twitter-follow
-----------------------------------

twitter-archiver will log all the tweets posted by any user since they
started posting. twitter-follow will print a list of all of all the
followers of a user (or all the users that user follows).


Programming with the Twitter api classes
========================================

The Twitter and TwitterStream classes are the key to building your own
Twitter-enabled applications.


The Twitter class
-----------------

The minimalist yet fully featured Twitter API class.

Get RESTful data by accessing members of this class. The result
is decoded python objects (lists and dicts).

The Twitter API is documented at:

**[https://dev.twitter.com/overview/documentation](https://dev.twitter.com/overview/documentation)**

Examples:
```python
from twitter import *

t = Twitter(
    auth=OAuth(token, token_key, con_secret, con_secret_key))

# Get your "home" timeline
t.statuses.home_timeline()

# Get a particular friend's timeline
t.statuses.user_timeline(screen_name="billybob")

# to pass in GET/POST parameters, such as `count`
t.statuses.home_timeline(count=5)

# to pass in the GET/POST parameter `id` you need to use `_id`
t.statuses.oembed(_id=1234567890)

# Update your status
t.statuses.update(
    status="Using @sixohsix's sweet Python Twitter Tools.")

# Send a direct message
t.direct_messages.new(
    user="billybob",
    text="I think yer swell!")

# Get the members of tamtar's list "Things That Are Rad"
t.lists.members(owner_screen_name="tamtar", slug="things-that-are-rad")

# An *optional* `_timeout` parameter can also be used for API
# calls which take much more time than normal or twitter stops
# responding for some reason:
t.users.lookup(
    screen_name=','.join(A_LIST_OF_100_SCREEN_NAMES), _timeout=1)

# Overriding Method: GET/POST
# you should not need to use this method as this library properly
# detects whether GET or POST should be used, Nevertheless
# to force a particular method, use `_method`
t.statuses.oembed(_id=1234567890, _method='GET')

# Send images along with your tweets:
# - first just read images from the web or from files the regular way:
with open("example.png", "rb") as imagefile:
    imagedata = imagefile.read()
# - then upload medias one by one on Twitter's dedicated server
#   and collect each one's id:
t_up = Twitter(domain='upload.twitter.com',
    auth=OAuth(token, token_key, con_secret, con_secret_key))
id_img1 = t_up.media.upload(media=imagedata)["media_id_string"]
id_img2 = t_up.media.upload(media=imagedata)["media_id_string"]
# - finally send your tweet with the list of media ids:
t.statuses.update(status="PTT ★", media_ids=",".join([id_img1, id_img2]))

# Or send a tweet with an image (or set a logo/banner similarily)
# using the old deprecated method that will probably disappear some day
params = {"media[]": imagedata, "status": "PTT ★"}
# Or for an image encoded as base64:
params = {"media[]": base64_image, "status": "PTT ★", "_base64": True}
t.statuses.update_with_media(**params)
```

Searching Twitter:
```python
# Search for the latest tweets about #pycon
t.search.tweets(q="#pycon")
```


Retrying after reaching the API rate limit
------------------------------------------

Simply create the `Twitter` instance with the argument `retry=True`, then the
HTTP error codes 429, 502, 503 and 504 will cause a retry of the last request.
If retry is an integer, it defines the number of retries attempted.


Using the data returned
-----------------------

Twitter API calls return decoded JSON. This is converted into
a bunch of Python lists, dicts, ints, and strings. For example:

```python
x = twitter.statuses.home_timeline()

# The first 'tweet' in the timeline
x[0]

# The screen name of the user who wrote the first 'tweet'
x[0]['user']['screen_name']
```

Getting raw XML data
--------------------

If you prefer to get your Twitter data in XML format, pass
format="xml" to the Twitter object when you instantiate it:

```python
twitter = Twitter(format="xml")
```

The output will not be parsed in any way. It will be a raw string
of XML.


The TwitterStream class
-----------------------

The TwitterStream object is an interface to the Twitter Stream
API. This can be used pretty much the same as the Twitter class
except the result of calling a method will be an iterator that
yields objects decoded from the stream. For example::

```python
twitter_stream = TwitterStream(auth=OAuth(...))
iterator = twitter_stream.statuses.sample()

for tweet in iterator:
    ...do something with this tweet...
```

Per default the ``TwitterStream`` object uses
[public streams](https://dev.twitter.com/docs/streaming-apis/streams/public).
If you want to use one of the other
[streaming APIs](https://dev.twitter.com/docs/streaming-apis), specify the URL
manually:

- [Public streams](https://dev.twitter.com/docs/streaming-apis/streams/public): stream.twitter.com
- [User streams](https://dev.twitter.com/docs/streaming-apis/streams/user): userstream.twitter.com
- [Site streams](https://dev.twitter.com/docs/streaming-apis/streams/site): sitestream.twitter.com

Note that you require the proper
[permissions](https://dev.twitter.com/docs/application-permission-model) to
access these streams. E.g. for direct messages your
[application](https://dev.twitter.com/apps) needs the "Read, Write & Direct
Messages" permission.

The following example demonstrates how to retrieve all new direct messages
from the user stream:

```python
auth = OAuth(
    consumer_key='[your consumer key]',
    consumer_secret='[your consumer secret]',
    token='[your token]',
    token_secret='[your token secret]'
)
twitter_userstream = TwitterStream(auth=auth, domain='userstream.twitter.com')
for msg in twitter_userstream.user():
    if 'direct_message' in msg:
        print msg['direct_message']['text']
```

The iterator will yield until the TCP connection breaks. When the
connection breaks, the iterator yields `{'hangup': True}`, and
raises `StopIteration` if iterated again.

Similarly, if the stream does not produce heartbeats for more than
90 seconds, the iterator yields `{'hangup': True,
'heartbeat_timeout': True}`, and raises `StopIteration` if
iterated again.

The `timeout` parameter controls the maximum time between
yields. If it is nonzero, then the iterator will yield either
stream data or `{'timeout': True}` within the timeout period. This
is useful if you want your program to do other stuff in between
waiting for tweets.

The `block` parameter sets the stream to be fully non-blocking. In
this mode, the iterator always yields immediately. It returns
stream data, or `None`. Note that `timeout` supercedes this
argument, so it should also be set `None` to use this mode, 
and non-blocking can potentially lead to 100% CPU usage.

Twitter Response Objects
------------------------

Response from a twitter request. Behaves like a list or a string
(depending on requested format) but it has a few other interesting
attributes.

`headers` gives you access to the response headers as an
httplib.HTTPHeaders instance. You can do
`response.headers.get('h')` to retrieve a header.

Authentication
--------------

You can authenticate with Twitter in three ways: NoAuth, OAuth, or
OAuth2 (app-only). Get help() on these classes to learn how to use them.

OAuth and OAuth2 are probably the most useful.


Working with OAuth
------------------

Visit the Twitter developer page and create a new application:

**[https://dev.twitter.com/apps/new](https://dev.twitter.com/apps/new)**

This will get you a CONSUMER_KEY and CONSUMER_SECRET.

When users run your application they have to authenticate your app
with their Twitter account. A few HTTP calls to twitter are required
to do this. Please see the twitter.oauth_dance module to see how this
is done. If you are making a command-line app, you can use the
oauth_dance() function directly.

Performing the "oauth dance" gets you an ouath token and oauth secret
that authenticate the user with Twitter. You should save these for
later so that the user doesn't have to do the oauth dance again.

read_token_file and write_token_file are utility methods to read and
write OAuth token and secret key values. The values are stored as
strings in the file. Not terribly exciting.

Finally, you can use the OAuth authenticator to connect to Twitter. In
code it all goes like this:

```python
from twitter import *

MY_TWITTER_CREDS = os.path.expanduser('~/.my_app_credentials')
if not os.path.exists(MY_TWITTER_CREDS):
    oauth_dance("My App Name", CONSUMER_KEY, CONSUMER_SECRET,
                MY_TWITTER_CREDS)

oauth_token, oauth_secret = read_token_file(MY_TWITTER_CREDS)

twitter = Twitter(auth=OAuth(
    oauth_token, oauth_token_secret, CONSUMER_KEY, CONSUMER_SECRET))

# Now work with Twitter
twitter.statuses.update(status='Hello, world!')
```

Working with OAuth2
-------------------

Twitter only supports the application-only flow of OAuth2 for certain
API endpoints. This OAuth2 authenticator only supports the application-only
flow right now.

To authenticate with OAuth2, visit the Twitter developer page and create a new
application:

**[https://dev.twitter.com/apps/new](https://dev.twitter.com/apps/new)**

This will get you a CONSUMER_KEY and CONSUMER_SECRET.

Exchange your CONSUMER_KEY and CONSUMER_SECRET for a bearer token using the
oauth2_dance function.

Finally, you can use the OAuth2 authenticator and your bearer token to connect
to Twitter. In code it goes like this::

```python
twitter = Twitter(auth=OAuth2(bearer_token=BEARER_TOKEN))

# Now work with Twitter
twitter.search.tweets(q='keyword')
```

License
=======

Python Twitter Tools are released under an MIT License.
