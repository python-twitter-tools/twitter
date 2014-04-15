# encoding: utf8

from random import choice
import time

from twitter import Twitter, NoAuth, OAuth, read_token_file
from twitter.cmdline import CONSUMER_KEY, CONSUMER_SECRET

noauth = NoAuth()
oauth = OAuth(*read_token_file('tests/oauth_creds')
              + (CONSUMER_KEY, CONSUMER_SECRET))

twitter1 = Twitter(domain='api.twitter.com',
                   auth=oauth,
                   api_version='1')

twitter11 = Twitter(domain='api.twitter.com',
                    auth=oauth,
                    api_version='1.1')

twitter_na = Twitter(domain='api.twitter.com', auth=noauth, api_version='1.1')

AZaz = "abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def get_random_str():
    return ''.join(choice(AZaz) for _ in range(10))


def test_v1_not_supported():
    # Arrange
    random_tweet = "Random tweet that shouldn't be posted " + get_random_str()

    # Act
    try:
        twitter1.statuses.update(status=random_tweet)
        time.sleep(2)
        error = False
    except:
        error = True

    # Assert
    assert error


def test_API_set_tweet():
    random_tweet = "A random tweet " + get_random_str()
    twitter11.statuses.update(status=random_tweet)
    time.sleep(2)
    recent = twitter11.statuses.user_timeline()
    assert recent
    assert isinstance(recent.rate_limit_remaining, int)
    assert isinstance(recent.rate_limit_reset, int)
    assert random_tweet == recent[0]['text']


def test_API_set_unicode_tweet():
    random_tweet = u"A random tweet with unicode üøπ" + get_random_str()
    twitter11.statuses.update(status=random_tweet)

    recent = twitter11.statuses.user_timeline()
    assert recent
    assert random_tweet == recent[0]['text']


def test_search():
    # In 1.1, search works on api.twitter.com not search.twitter.com
    # and requires authorisation
    results = twitter11.search(q='foo')
    assert results


def test_get_trends():
    # This is one method of inserting parameters, using named
    # underscore params.
    world_trends = twitter11.trends._woeid(_woeid=1)
    assert world_trends


def test_get_trends_2():
    # This is a nicer variation of the same call as above.
    world_trends = twitter11.trends._(1)
    assert world_trends


def test_get_trends_3():
    # Of course they broke it all again in 1.1...
    assert twitter11.trends.place(_id=1)

# End of file
