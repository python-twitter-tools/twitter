
from twitter.api2 import get, search, TwitterAPI, TwitterError

from .test_sanity import oauth, get_random_str


api = TwitterAPI(auth=oauth)

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
    assert results


def test_can_do_oauth():
    results = api.get("statuses/home_timeline")
    assert results


def test_handle_404():
    try:
        get("garbage")
        assert False
    except TwitterError as e:
        pass


def test_handle_not_authenticated():
    try:
        get("statuses/home_timeline")
        assert False
    except TwitterError as e:
        pass


def test_post_a_new_tweet():
    api.post("statuses/update", status=get_random_str() + "ïõ")


def test_can_get_raw_response():
    raw_api = TwitterAPI(return_raw_response=True)
    res = raw_api.get("statuses/public_timeline")
    assert res
    assert res.headers
    assert res.json
