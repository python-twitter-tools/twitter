# encoding: utf-8

from twitter.api2 import TwitterAPI, TwitterError

from .test_sanity import oauth, get_random_str

noauth_api = TwitterAPI()
api = TwitterAPI(auth=oauth, secure=True)
stream_api = TwitterAPI(domain="stream.twitter.com", auth=oauth, stream=True,
                        secure=True)


def test_can_get_specific_status():
    update = api.get('statuses/show/:id', id=230400277440770048)
    assert update


def test_can_do_oauth():
    results = api.get("statuses/home_timeline")
    assert results


def test_handle_404():
    try:
        noauth_api.get("garbage")
        assert False
    except TwitterError as e:
        pass


def test_handle_not_authenticated():
    try:
        noauth_api.get("statuses/home_timeline")
        assert False
    except TwitterError as e:
        pass


def test_post_a_new_tweet():
    api.post("statuses/update", status=get_random_str() + u"ïõ")


def test_can_get_raw_response():
    raw_api = TwitterAPI(return_raw_response=True, auth=oauth)
    res = raw_api.get("statuses/home_timeline")
    assert res
    assert res.headers
    assert res.json


def test_can_stream_some_tweets():
    itr = stream_api.get("statuses/sample")
    tweets = 0
    for tweet in itr:
        assert tweet
        tweets += 1
        if tweets > 2:
            return

