# encoding: utf-8
from __future__ import unicode_literals

import os
from random import choice
import time
import pickle
import json

from twitter import Twitter, NoAuth, OAuth, read_token_file, TwitterHTTPError
from twitter.api import TwitterDictResponse, TwitterListResponse
from twitter.cmdline import CONSUMER_KEY, CONSUMER_SECRET

noauth = NoAuth()
oauth = OAuth(*read_token_file('tests/oauth_creds')
              + (CONSUMER_KEY, CONSUMER_SECRET))

twitter11 = Twitter(domain='api.twitter.com',
                    auth=oauth,
                    api_version='1.1')

twitter11_na = Twitter(domain='api.twitter.com',
                       auth=noauth,
                       api_version='1.1')

AZaz = "abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def get_random_str():
    return ''.join(choice(AZaz) for _ in range(10))


def test_API_set_tweet(unicod=False):
    random_tweet = "A random tweet %s" % \
        ("with unicode üøπ" if unicod else "") + get_random_str()
    twitter11.statuses.update(status=random_tweet)
    time.sleep(5)
    recent = twitter11.statuses.home_timeline()
    assert recent
    assert isinstance(recent.rate_limit_remaining, int)
    assert isinstance(recent.rate_limit_reset, int)
    texts = [tweet['text'] for tweet in recent]
    assert random_tweet in texts

def test_API_set_unicode_tweet():
    test_API_set_tweet(unicod=True)


def clean_link(text):
    pos = text.find(" http://t.co")
    if pos != -1:
        return text[:pos]
    return text

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

def test_API_set_unicode_twitpic(base64=False):
    random_tweet = "A random twitpic from %s with unicode üøπ" % \
                    ("base64" if base64 else "file") + get_random_str()
    if base64:
        img = b"iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAIAAACQkWg2AAAAAXNSR0IArs4c6QAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB94JFhMBAJv5kaUAAAAZdEVYdENvbW1lbnQAQ3JlYXRlZCB3aXRoIEdJTVBXgQ4XAAAA4UlEQVQoz7WSIZLGIAxG6c5OFZjianBcIOfgPkju1DsEBWfAUEcNGGpY8Xe7dDoVFRvHfO8NJGRorZE39UVe1nd/WNfVObcsi3OOEAIASikAmOf5D2q/FWPUWgshKKWfiFIqhNBaxxhPjPQ05/z+Bs557xw9hBC89ymlu5BS8t6HEC5NW2sR8alRRLTWXoRSSinlSejT12M9BAAAgCeoTw9BSimlfBIu6WdYtVZEVErdaaUUItZaL/9wOsaY83YAMMb0dGtt6Jdv3/ec87ZtOWdCCGNsmibG2DiOJzP8+7b+AAOmsiPxyHWCAAAAAElFTkSuQmCC"
    else:
        with open(os.path.join(__location__, "test.png"), "rb") as f:
            img = f.read()
    params = {"status": random_tweet, "media[]": img}
    if base64:
        params["_base64"] = True
    twitter11.statuses.update_with_media(**params)
    time.sleep(5)
    recent = twitter11.statuses.home_timeline()
    assert recent
    texts = [clean_link(tweet['text']) for tweet in recent]
    assert random_tweet in texts

def test_API_set_unicode_twitpic_base64():
    test_API_set_unicode_twitpic(base64=True)


def test_search():
    # In 1.1, search works on api.twitter.com not search.twitter.com
    # and requires authorisation
    results = twitter11.search.tweets(q='foo')
    assert results


def test_get_trends():
    # This is one method of inserting parameters, using named
    # underscore params.
    world_trends = twitter11.trends.available(_woeid=1)
    assert world_trends


def test_get_trends_2():
    # This is a nicer variation of the same call as above.
    world_trends = twitter11.trends._(1)
    assert world_trends


def test_get_trends_3():
    # Of course they broke it all again in 1.1...
    assert twitter11.trends.place(_id=1)


def test_TwitterHTTPError_raised_for_invalid_oauth():
    test_passed = False
    try:
        twitter11_na.statuses.mentions_timeline()
    except TwitterHTTPError:
        # this is the error we are looking for :)
        test_passed = True
    assert test_passed


def test_picklability():
    res = TwitterDictResponse({'a': 'b'})
    p = pickle.dumps(res)
    res2 = pickle.loads(p)
    assert res == res2
    assert res2['a'] == 'b'

    res = TwitterListResponse([1, 2, 3])
    p = pickle.dumps(res)
    res2 = pickle.loads(p)
    assert res == res2
    assert res2[2] == 3


def test_jsonifability():
    res = TwitterDictResponse({'a': 'b'})
    p = json.dumps(res)
    res2 = json.loads(p)
    assert res == res2
    assert res2['a'] == 'b'

    res = TwitterListResponse([1, 2, 3])
    p = json.dumps(res)
    res2 = json.loads(p)
    assert res == res2
    assert res2[2] == 3
