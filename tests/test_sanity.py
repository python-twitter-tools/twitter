# encoding: utf8

from random import choice
import time

from twitter import Twitter, NoAuth, OAuth, read_token_file, TwitterHTTPError
from twitter.cmdline import CONSUMER_KEY, CONSUMER_SECRET

noauth = NoAuth()
oauth = OAuth(*read_token_file('tests/oauth_creds')
               + (CONSUMER_KEY, CONSUMER_SECRET))

twitter11 = Twitter(domain='api.twitter.com',
                    auth=oauth,
                    api_version='1.1')
twitter11_na = Twitter(domain='api.twitter.com', auth=noauth, api_version='1.1')


AZaz = "abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def get_random_str():
    return ''.join(choice(AZaz) for _ in range(10))


def test_API_set_tweet():
    random_tweet = "A random tweet " + get_random_str()
    twitter11.statuses.update(status=random_tweet)
    time.sleep(2)
    recent = twitter11.statuses.home_timeline()
    assert recent
    assert isinstance(recent.rate_limit_remaining, int)
    assert isinstance(recent.rate_limit_reset, int)
    assert random_tweet == recent[0]['text']


def test_API_set_unicode_tweet():
    random_tweet = u"A random tweet with unicode üøπ" + get_random_str()
    twitter11.statuses.update(status=random_tweet)

    recent = twitter11.statuses.home_timeline()
    assert recent
    assert random_tweet == recent[0]['text']


def test_search():
    results = twitter11.search.tweets(q='foo')
    assert results


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
