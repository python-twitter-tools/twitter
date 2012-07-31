
from twitter import OAuth
from twitter.api2 import get, search, TwitterAPI

def test_can_get_public_tweet_json():
    updates = get('statuses/public_timeline')
    assert updates
    assert updates[0]['text']


def test_can_get_specific_status():
    update = get('statuses/show/:id', id=230400277440770048)
    assert update


def test_can_perform_a_search():
    results = TwitterAPI(host="search.twitter.com", api_ver=None).get(
        'search', q="hello")
    assert results


def test_can_do_an_easy_search():
    results = search("hello")
