# encoding: utf8

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


def tweet_in_recent(tweet, recent_tweets):
    for recent in recent_tweets:
        if tweet == recent['text']:
            return True
    return False


def test_API_set_tweet():
    random_tweet = "A random tweet " + get_random_str()
    twitter11.statuses.update(status=random_tweet)
    time.sleep(2)
    recent = twitter11.statuses.home_timeline()
    assert recent
    assert isinstance(recent.rate_limit_remaining, int)
    assert isinstance(recent.rate_limit_reset, int)
    assert tweet_in_recent(random_tweet, recent)


def test_API_set_unicode_tweet():
    random_tweet = u"A random tweet with unicode üøπ" + get_random_str()
    twitter11.statuses.update(status=random_tweet)

    recent = twitter11.statuses.home_timeline()
    assert recent
    assert tweet_in_recent(random_tweet, recent)


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

# End of file
