Python Twitter Tools
====================

[![Tests](https://github.com/python-twitter-tools/twitter/workflows/Tests/badge.svg)](https://github.com/python-twitter-tools/twitter/actions)
[![Coverage Status](https://coveralls.io/repos/github/python-twitter-tools/twitter/badge.svg?branch=master)](https://coveralls.io/github/python-twitter-tools/twitter?branch=master)

The Minimalist Twitter API for Python is a Python API for Twitter,
everyone's favorite Web 2.0 Facebook-style status updater for people
on the go.

Also included is a Twitter command-line tool for getting your friends'
tweets and setting your own tweet from the safety and security of your
favorite shell and an IRC bot that can announce Twitter updates to an
IRC channel.

For more information:

 * install the [package](https://pypi.org/project/twitter/) `pip install twitter`
 * import the `twitter` package and run `help()` on it
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

The IRC bot is associated with a Twitter account (either your own account or an
account you create for the bot). The bot announces all tweets from friends
it is following. It can be made to follow or leave friends through IRC /msg
commands.


`twitter-log`
-------------

`twitter-log` is a simple command-line tool that dumps all public
tweets from a given user in a simple text format. It is useful to get
a complete offsite backup of all your tweets. Run `twitter-log` and
read the instructions.

`twitter-archiver` and `twitter-follow`
---------------------------------------

twitter-archiver will log all the tweets posted by any user since they
started posting. twitter-follow will print a list of all of all the
followers of a user (or all the users that user follows).


Programming with the Twitter API classes
========================================

The `Twitter` and `TwitterStream` classes are the key to building your own
Twitter-enabled applications.


The `Twitter` class
-------------------

The minimalist yet fully featured Twitter API class.

Get RESTful data by accessing members of this class. The result
is decoded python objects (lists and dicts).

The Twitter API is documented at:

**[https://developer.twitter.com/en/docs](https://developer.twitter.com/en/docs)**

The list of most accessible functions is listed at:

**[https://developer.twitter.com/en/docs/api-reference-index](https://developer.twitter.com/en/docs/api-reference-index)**

Examples:

```python
from twitter import *

t = Twitter(
    auth=OAuth(token, token_secret, consumer_key, consumer_secret))

# Get your "home" timeline
t.statuses.home_timeline()

# Get a particular friend's timeline
t.statuses.user_timeline(screen_name="boogheta")

# to pass in GET/POST parameters, such as `count`
t.statuses.home_timeline(count=5)

# to pass in the GET/POST parameter `id` you need to use `_id`
t.statuses.show(_id=1234567890)

# Update your status
t.statuses.update(
    status="Using @boogheta's sweet Python Twitter Tools.")

# Send a direct message
t.direct_messages.events.new(
    _json={
        "event": {
            "type": "message_create",
            "message_create": {
                "target": {
                    "recipient_id": t.users.show(screen_name="boogheta")["id"]},
                "message_data": {
                    "text": "I think yer swell!"}}}})

# Get the members of maxmunnecke's list "network analysis tools" (grab the list_id within the url) https://twitter.com/i/lists/1130857490764091392
t.lists.members(owner_screen_name="maxmunnecke", list_id="1130857490764091392")

# Favorite/like a status
status = t.statuses.home_timeline()[0]
if not status['favorited']:
    t.favorites.create(_id=status['id'])

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
t_upload = Twitter(domain='upload.twitter.com',
    auth=OAuth(token, token_secret, consumer_key, consumer_secret))
id_img1 = t_upload.media.upload(media=imagedata)["media_id_string"]
id_img2 = t_upload.media.upload(media=imagedata)["media_id_string"]
# - finally send your tweet with the list of media ids:
t.statuses.update(status="PTT ★", media_ids=",".join([id_img1, id_img2]))

# Or send a tweet with an image (or set a logo/banner similarly)
# using the old deprecated method that will probably disappear some day
params = {"media[]": imagedata, "status": "PTT ★"}
# Or for an image encoded as base64:
params = {"media[]": base64_image, "status": "PTT ★", "_base64": True}
t.statuses.update_with_media(**params)

# Attach text metadata to medias sent, using the upload.twitter.com route
# using the _json workaround to send json arguments as POST body
# (warning: to be done before attaching the media to a tweet)
t_upload.media.metadata.create(_json={
  "media_id": id_img1,
  "alt_text": { "text": "metadata generated via PTT!" }
})
# or with the shortcut arguments ("alt_text" and "text" work):
t_upload.media.metadata.create(media_id=id_img1, text="metadata generated via PTT!")

# Alternatively, you can reuse the originally instantiated object, 
# changing the domain, that is:
t.domain = 'upload.twitter.com'

# Now you can upload the image (or images).
id_img1 = t.media.upload(media=imagedata)['media_id_string']
id_img2 = t.media.upload(media=imagedata)["media_id_string"]

# You now can reset the domain to the original one:
t.domain = 'api.twitter.com'

# And you can send the update:
t.statuses.update(status="PTT ★", media_ids=",".join([id_img1, id_img2]))


```

Searching Twitter:
```python
# Search for the latest tweets about #pycon
t.search.tweets(q="#pycon")

# Search for the latest tweets about #pycon, using [extended mode](https://developer.twitter.com/en/docs/tweets/tweet-updates)
t.search.tweets(q="#pycon", tweet_mode='extended')
```


Retrying after reaching the API rate limit
------------------------------------------

Simply create the `Twitter` instance with the argument `retry=True`, then the
HTTP error codes `429`, `502`, `503`, and `504` will cause a retry of the last
request.

If `retry` is an integer, it defines the maximum number of retry attempts.


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
`format="xml"` to the `Twitter` object when you instantiate it:

```python
twitter = Twitter(format="xml")
```

The output will not be parsed in any way. It will be a raw string
of XML.

The `TwitterStream` class
-------------------------

The `TwitterStream` object is an interface to the Twitter Stream
API. This can be used pretty much the same as the `Twitter` class,
except the result of calling a method will be an iterator that
yields objects decoded from the stream. For example::

```python
twitter_stream = TwitterStream(auth=OAuth(...))
iterator = twitter_stream.statuses.sample()

for tweet in iterator:
    ...do something with this tweet...
```

Per default the `TwitterStream` object uses
[public streams](https://dev.twitter.com/docs/streaming-apis/streams/public).
If you want to use one of the other
[streaming APIs](https://dev.twitter.com/docs/streaming-apis), specify the URL
manually.

The iterator will `yield` until the TCP connection breaks. When the
connection breaks, the iterator yields `{'hangup': True}` (and
raises `StopIteration` if iterated again).

Similarly, if the stream does not produce heartbeats for more than
90 seconds, the iterator yields `{'hangup': True,
'heartbeat_timeout': True}` (and raises `StopIteration` if
iterated again).

The `timeout` parameter controls the maximum time between
yields. If it is nonzero, then the iterator will yield either
stream data or `{'timeout': True}` within the timeout period. This
is useful if you want your program to do other stuff in between
waiting for tweets.

The `block` parameter sets the stream to be fully non-blocking.
In this mode, the iterator always yields immediately. It returns
stream data, or `None`.

Note that `timeout` supercedes this argument, so it should also be
set `None` to use this mode, and non-blocking can potentially lead
to 100% CPU usage.

Twitter `Response` Objects
--------------------------

Response from a Twitter request. Behaves like a list or a string
(depending on requested format), but it has a few other interesting
attributes.

`headers` gives you access to the response headers as an
`httplib.HTTPHeaders` instance. Use `response.headers.get('h')`
to retrieve a header.

Authentication
--------------

You can authenticate with Twitter in three ways: NoAuth, OAuth, or
OAuth2 (app-only). Get `help()` on these classes to learn how to use them.

OAuth and OAuth2 are probably the most useful.


Working with OAuth
------------------

Visit the Twitter developer page and create a new application:

**[https://dev.twitter.com/apps/new](https://dev.twitter.com/apps/new)**

This will get you a `CONSUMER_KEY` and `CONSUMER_SECRET`.

When users run your application they have to authenticate your app
with their Twitter account. A few HTTP calls to Twitter are required
to do this. Please see the `twitter.oauth_dance` module to see how this
is done. If you are making a command-line app, you can use the
`oauth_dance()` function directly.

Performing the "oauth dance" gets you an oauth token and oauth secret
that authenticate the user with Twitter. You should save these for
later, so that the user doesn't have to do the oauth dance again.

`read_token_file` and `write_token_file` are utility methods to read and
write OAuth `token` and `secret` key values. The values are stored as
strings in the file. Not terribly exciting.

Finally, you can use the `OAuth` authenticator to connect to Twitter. In
code it all goes like this:

```python
from twitter import *

MY_TWITTER_CREDS = os.path.expanduser('~/.my_app_credentials')
if not os.path.exists(MY_TWITTER_CREDS):
    oauth_dance("My App Name", CONSUMER_KEY, CONSUMER_SECRET,
                MY_TWITTER_CREDS)

oauth_token, oauth_secret = read_token_file(MY_TWITTER_CREDS)

twitter = Twitter(auth=OAuth(
    oauth_token, oauth_secret, CONSUMER_KEY, CONSUMER_SECRET))

# Now work with Twitter
twitter.statuses.update(status='Hello, world!')
```

Working with `OAuth2`
---------------------

Twitter only supports the application-only flow of OAuth2 for certain
API endpoints. This OAuth2 authenticator only supports the application-only
flow right now.

To authenticate with OAuth2, visit the Twitter developer page and create a new
application:

**[https://dev.twitter.com/apps/new](https://dev.twitter.com/apps/new)**

This will get you a `CONSUMER_KEY` and `CONSUMER_SECRET`.

Exchange your `CONSUMER_KEY` and `CONSUMER_SECRET` for a bearer token using the
`oauth2_dance` function.

Finally, you can use the `OAuth2` authenticator and your bearer token to connect
to Twitter. In code it goes like this::

```python
twitter = Twitter(auth=OAuth2(bearer_token=BEARER_TOKEN))

# Now work with Twitter
twitter.search.tweets(q='keyword')
```

License
=======

Python Twitter Tools are released under an MIT License.
