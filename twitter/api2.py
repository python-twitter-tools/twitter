"""
api2 is a simpler, more predictable means of working with the Twitter
API in Python. It has the following improvements over the old API:

 - more reliable connections, thanks to the Requests library
 - simpler calling conventions
 - no confusion between GET and POST


Simple API Requests
===================

You can perform unauthenticated get requests using the `get`
function. To get some tweets from the public timeline::

    from twitter.api2 import get
    tweets = get("statuses/public_timeline")

The string "statuses/public_timeline" is found in the Twitter API
documentation: https://dev.twitter.com/docs/api

Any keyword arguments to `get` are turned into parameters sent to
Twitter. That is, unless one of the parameters matches part of the
URI, in which case it will be inserted::

    retweets = get("statuses/:id/retweeted_by",
                   id=230429161729163264,
                   count=3)

This returns a list of people who retweeted the tweet with the given
id. id gets inserted into the URL where :id is. Count is passed as a
parameter to control the max number of retweets to get. So, the
specifically generated URL is:

    http://api.twitter.com/1/statuses/230429161729163264/retweeted_by.json?count=3

The point of using Python Twitter Tools is that you don't have to care
about the specific URL.


Results
=======

Twitter API calls return decoded JSON. This is converted into Python
lists, dicts, ints, and strings. For example::

    tweets = get("statuses/public_timeline")

    # The first 'tweet' in the timeline
    tweets[0]

    # The screen name of the user who wrote the first 'tweet'
    tweets[0]['user']['screen_name']


Searching
=========

The search helper function will search twitter very easily::

    from twitter.api2 import search
    results = search("my search string")


Authentication
==============

The Twitter API is limited unless you are authenticated. Assuming you
have an OAuth authentication object, you can do authenticated calls
like this::

    from twitter.api2 import TwitterAPI
    api = TwitterAPI(auth=oauth)

    # Get tweets in your timeline:
    api.get("statuses/home_timeline")

    # Post a tweet to your timeline
    api.post("statuses/update",
             status="Using @sixohsix's Python Twitter Tools api2")

The TwitterAPI's `get` and `post` methods work just like the `get`
function described above.
"""


import requests
import json

from .api import TwitterError
from .auth import NoAuth


class TwitterAPIError(TwitterError):
    def __init__(self, message, res):
        self.res = res
        TwitterError.__init__(self, message)


class TwitterAPI(object):
    def __init__(self, host='api.twitter.com', api_ver='1', auth=NoAuth(),
                 secure=True, stream=False, return_raw_response=False):
        """
        `host`        host to connect to (api.twitter.com)
        `api_ver`     API version
        """
        self.host = host
        self.api_ver = api_ver
        self.auth = auth
        self.secure = secure
        self.stream = stream
        self.return_raw_response = return_raw_response


    def get(self, path, **kwargs):
        url, remaining_params = make_url(self.secure, self.host, self.api_ver,
                                         path, kwargs)
        data = self.auth.encode_params(url, 'GET', remaining_params)
        headers = self.auth.generate_headers()
        res = requests.get(url + '?' + data, headers=headers, prefetch=(not self.stream))
        return handle_res(res, self.return_raw_response, self.stream)


    def post(self, path, **kwargs):
        url, remaining_params = make_url(self.secure, self.host, self.api_ver,
                                         path, kwargs)
        data = self.auth.encode_params(url, 'POST', remaining_params)
        headers = self.auth.generate_headers()
        res = requests.post(url, data=data, headers=headers, prefetch=(not self.stream))
        return handle_res(res, self.return_raw_response, self.stream)


_default_api = TwitterAPI()

get = _default_api.get


_search_api = TwitterAPI(host="search.twitter.com", api_ver=None)

def search(q, **kwargs):
    return _search_api.get("search", q=q, **kwargs)


def make_url(secure, host, api_ver, path, params):
    remaining_params = dict(params)
    real_params = []
    for param in path.split('/'):
        if param.startswith(':'):
            if param[1:] not in params:
                raise TwitterError("Missing parameter for ':{}'".format(param))
            param = str(params.pop(param[1:]))
        real_params.append(param)
    real_path = '/'.join(real_params)
    api_ver_str = '{}/'.format(str(api_ver)) if api_ver is not None else ""
    secure_str = 's' if secure else ''
    url = 'http{}://{}/{}{}.json'.format(secure_str, host, str(api_ver_str),
                                         real_path)
    return url, remaining_params


def handle_res(res, return_raw_response, stream):
    if res.status_code != 200:
        raise TwitterAPIError(
            "Twitter responded with invalid status code: {}"
            .format(res.status_code),
            res)
    if return_raw_response:
        result = res
    elif stream:
        def generate_json():
            for line in res.iter_lines():
                yield json.loads(line.decode('utf-8'))
        return generate_json()
    else:
        result = res.json
    return result
