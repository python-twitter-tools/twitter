# encoding: utf-8
from __future__ import unicode_literals

import os
from random import choice
import time
import pickle
import json

from twitter import Twitter, NoAuth, OAuth, read_token_file, TwitterHTTPError
from twitter.api import TwitterDictResponse, TwitterListResponse, POST_ACTIONS, method_for_uri
from twitter.cmdline import CONSUMER_KEY, CONSUMER_SECRET

noauth = NoAuth()
oauth = OAuth(*read_token_file('tests/oauth_creds')
              + (CONSUMER_KEY, CONSUMER_SECRET))

twitter11 = Twitter(domain='api.twitter.com',
                    auth=oauth,
                    api_version='1.1')

twitter_upl = Twitter(domain='upload.twitter.com',
                      auth=oauth,
                      api_version='1.1')

twitter11_na = Twitter(domain='api.twitter.com',
                       auth=noauth,
                       api_version='1.1')

AZaz = "abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ"

b64_image_data = b"iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAIAAACQkWg2AAAAAXNSR0IArs4c6QAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB94JFhMBAJv5kaUAAAAZdEVYdENvbW1lbnQAQ3JlYXRlZCB3aXRoIEdJTVBXgQ4XAAAA4UlEQVQoz7WSIZLGIAxG6c5OFZjianBcIOfgPkju1DsEBWfAUEcNGGpY8Xe7dDoVFRvHfO8NJGRorZE39UVe1nd/WNfVObcsi3OOEAIASikAmOf5D2q/FWPUWgshKKWfiFIqhNBaxxhPjPQ05/z+Bs557xw9hBC89ymlu5BS8t6HEC5NW2sR8alRRLTWXoRSSinlSejT12M9BAAAgCeoTw9BSimlfBIu6WdYtVZEVErdaaUUItZaL/9wOsaY83YAMMb0dGtt6Jdv3/ec87ZtOWdCCGNsmibG2DiOJzP8+7b+AAOmsiPxyHWCAAAAAElFTkSuQmCC"

def get_random_str():
    return ''.join(choice(AZaz) for _ in range(10))


def test_API_set_tweet(unicod=False):
    random_tweet = "A random tweet %s" % \
        ("with unicode üøπ" if unicod else "") + get_random_str()
    twitter11.statuses.update(status=random_tweet)
    time.sleep(5)
    recent = twitter11.statuses.user_timeline()
    assert recent
    assert isinstance(recent.rate_limit_remaining, int)
    assert isinstance(recent.rate_limit_reset, int)
    texts = [tweet['text'] for tweet in recent]
    assert random_tweet in texts

def test_API_set_unicode_tweet():
    test_API_set_tweet(unicod=True)


def clean_link(text):
    pos = text.find(" https://t.co")
    if pos != -1:
        return text[:pos]
    return text

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

def _img_data():
    return open(os.path.join(__location__, "test.png"), "rb").read()

def _test_API_old_media(img, _base64):
    random_tweet = (
        "A random twitpic with unicode üøπ"
        + get_random_str())
    params = {"status": random_tweet, "media[]": img, "_base64": _base64}
    twitter11.statuses.update_with_media(**params)
    time.sleep(5)
    recent = twitter11.statuses.user_timeline()
    assert recent
    texts = [clean_link(tweet['text']) for tweet in recent]
    assert random_tweet in texts

def test_API_set_unicode_twitpic_base64():
    _test_API_old_media(b64_image_data, True)

def test_API_set_unicode_twitpic_base64_string():
    _test_API_old_media(b64_image_data.decode('utf-8'), True)

def test_API_set_unicode_twitpic_auto_base64_convert():
    _test_API_old_media(_img_data(), False)

def _test_upload_media():
    res = twitter_upl.media.upload(media=_img_data())
    assert res
    assert res["media_id"]
    return str(res["media_id"])

def test_multitwitpic():
    pics = [_test_upload_media(), _test_upload_media(), _test_upload_media()]
    random_tweet = ("I can even tweet multiple pictures at once now! ★  "
        + get_random_str())
    res = twitter11.statuses.update(status=random_tweet, media_ids=",".join(pics))
    assert res
    assert res["extended_entities"]
    assert len(res["extended_entities"]["media"]) == len(pics)
    recent = twitter11.statuses.user_timeline()
    assert recent
    texts = [clean_link(t['text']) for t in recent]
    assert random_tweet in texts

def test_metadatapic():
    pic = _test_upload_media()
    metadata = "metadata generated via PTT! ★" + get_random_str()
    res = twitter_upl.media.metadata.create(_json={
        "media_id": pic,
        "alt_text": { "text": metadata }
    })
    random_tweet = ("I can also tweet pictures with text metadata attached ★  "
        + get_random_str())
    res = twitter11.statuses.update(status=random_tweet, media_ids=pic)
    assert res
    recent = twitter11.statuses.user_timeline(include_ext_alt_text=True, include_entities=True)
    assert recent
    meta = recent[0].get("extended_entities", {}).get("media")
    assert meta
    assert metadata == meta[0].get("ext_alt_text", "")

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


def test_method_for_uri():
    for action in POST_ACTIONS:
        assert method_for_uri(get_random_str() + '/' + action) == 'POST'
    assert method_for_uri('statuses/timeline') == 'GET'
