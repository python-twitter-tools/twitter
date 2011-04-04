
from random import choice

from twitter import Twitter, NoAuth, OAuth, read_token_file
from twitter.cmdline import CONSUMER_KEY, CONSUMER_SECRET

noauth = NoAuth()
oauth = OAuth(*read_token_file('tests/oauth_creds')
               + (CONSUMER_KEY, CONSUMER_SECRET))

twitter = Twitter(domain='api.twitter.com',
                  auth=oauth,
                  api_version='1')
twitter_na = Twitter(domain='api.twitter.com', auth=noauth, api_version='1')


AZaz = "abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def get_random_str():
    return ''.join(choice(AZaz) for _ in range(10))


def test_API_get_some_public_tweets():
    updates = twitter_na.statuses.public_timeline()
    assert updates
    assert updates[0]['created_at']


def test_API_set_tweet():
    random_tweet = "A random tweet " + get_random_str()
    twitter.statuses.update(status=random_tweet)

    recent = twitter.statuses.user_timeline()
    assert recent
    assert random_tweet == recent[0]['text']


def test_API_friendship_exists():
    assert True == twitter.friendships.exists(
        user_a='ptttest0001', user_b='sixohsix')
    assert False == twitter.friendships.exists(
        user_a='gruber', user_b='ptttest0001')


def test_search():
    t_search = Twitter(domain='search.twitter.com')
    results = t_search.search(q='foo')
    assert results
