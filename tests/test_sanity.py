# encoding: utf-8
from __future__ import print_function
from __future__ import unicode_literals

import os
from random import choice
import time
import pickle
import json
import sys

from twitter import Twitter, TwitterStream, TwitterStream2, NoAuth, OAuth, OAuth2, read_token_file, TwitterHTTPError
from twitter.api import TwitterDictResponse, TwitterListResponse, POST_ACTIONS, method_for_uri

noauth = NoAuth()

try:
    api_keys = (
      os.environ['OAUTH_TOKEN'],
      os.environ['OAUTH_SECRET'],
      os.environ['CONSUMER_KEY'],
      os.environ['CONSUMER_SECRET']
    )
    bearer_token = os.environ['BEARER_TOKEN']
except:
    try:
        api_keys = (read_token_file('tests/oauth_creds') +
                   read_token_file('tests/consumer_creds'))
        with open('tests/bearer_token')as f:
            bearer_token = f.readline().strip()
    except Exception as e:
        print("ERROR: could not find API keys neither as environment variable nor as local tests/oauth_creds, tests/consumer_creds and tests/bearer_token files", file=sys.stderr)
        exit(1)

oauth = OAuth(*api_keys)
oauth2 = OAuth2(bearer_token=bearer_token)

twitter11 = Twitter(domain='api.twitter.com',
                    auth=oauth,
                    api_version='1.1')

twitter11_upl = Twitter(domain='upload.twitter.com',
                      auth=oauth,
                      api_version='1.1')

twitter11_app = Twitter(domain='api.twitter.com',
                    auth=oauth2,
                    api_version='1.1')

twitter11_na = Twitter(domain='api.twitter.com',
                       auth=noauth,
                       api_version='1.1')

twitter11_stream = TwitterStream(domain='stream.twitter.com',
                    auth=oauth,
                    api_version='1.1')

twitter2 = Twitter(domain='api.twitter.com',
                    auth=oauth,
                    api_version='2',
                    format='')

twitter2_app = Twitter(domain='api.twitter.com',
                    auth=oauth2,
                    api_version='2',
                    format='')

twitter2_stream = TwitterStream2(domain='api.twitter.com',
                    auth=oauth2,
                    api_version='2')

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


def _test_API_set_unicode_twitpic_base64():
    _test_API_old_media(b64_image_data, True)


def _test_API_set_unicode_twitpic_base64_string():
    _test_API_old_media(b64_image_data.decode('utf-8'), True)


def _test_API_set_unicode_twitpic_auto_base64_convert():
    _test_API_old_media(_img_data(), False)


def _test_upload_media():
    res = twitter11_upl.media.upload(media=_img_data())
    assert res
    assert res["media_id"]
    return str(res["media_id"])


def test_metadata_multipic():
    pics = [_test_upload_media(), _test_upload_media(), _test_upload_media()]
    metadata = "metadata generated via PTT! ★" + get_random_str()
    res = twitter11_upl.media.metadata.create(media_id=pics[0], text=metadata)
    random_tweet = ("I can even tweet multiple pictures at once and attach metadata onto some! ★  "
        + get_random_str())
    res = twitter11.statuses.update(status=random_tweet, media_ids=",".join(pics))
    assert res
    assert res["extended_entities"]
    assert len(res["extended_entities"]["media"]) == len(pics)
    time.sleep(5)
    recent = twitter11.statuses.user_timeline(include_ext_alt_text=True, include_entities=True, count=20)
    assert recent
    texts = [clean_link(t['text']) for t in recent]
    assert random_tweet in texts
    meta = recent[0].get("extended_entities", {}).get("media")
    assert meta
    assert metadata == meta[0].get("ext_alt_text", "")


def _test_get_tweet(results):
    assert results
    if "data" in results:
        results = results["data"]
    assert len(results)
    result = results[0]
    assert result.get("full_text", result.get("text")) == "If you're interacting with Twitter via Python, I'd recommend Python Twitter Tools by @sixohsix https://github.com/sixohsix/twitter"


def test_get_tweet():
    _test_get_tweet(twitter11.statuses.lookup(_id='27095053386121216', include_entities="true", tweet_mode="extended"))


def test_get_tweet_app_auth():
    _test_get_tweet(twitter11_app.statuses.lookup(_id='27095053386121216', include_entities="true", tweet_mode="extended"))


def test_get_tweet_v2():
    _test_get_tweet(twitter2.tweets(ids='27095053386121216', params={"tweet.fields": "text"}))


def test_get_tweet_v2_app_auth():
    _test_get_tweet(twitter2_app.tweets(ids='27095053386121216', params={"tweet.fields": "text"}))


def test_search():
    # In 1.1, search works on api.twitter.com not search.twitter.com
    # and requires authorisation
    results = twitter11.search.tweets(q='foo')
    assert results


def test_stream():
    # Sometimes Twitter matches tweets with keywords from urls or users
    # which are more complex to check so we allow a few mismatches
    mismatch = 0
    for tweet in twitter11_stream.statuses.filter(track="gaga,bieber", filter_level='none', stall_warnings='true'):
        if "timeout" in tweet:
            continue
        assert "text" in tweet
        lowtext = tweet["text"].lower()
        if "gaga" in lowtext or "bieber" in lowtext:
            break
        mismatch += 1
        if mismatch > 5:
            assert "gaga" in lowtext or "bieber" in lowtext


def test_stream_v2():
    rules = twitter2_app.tweets.search.stream.rules()
    assert "data" in rules and "meta" in rules and len(rules["data"]) == rules["meta"].get("result_count", 0)

    if len(rules["data"]):
        remove = twitter2_app.tweets.search.stream.rules(
            _json={"delete": {"ids": [rule["id"] for rule in rules["data"]]}}
        )
        assert "meta" in remove and "summary" in remove["meta"] and remove["meta"]["summary"].get("deleted", 0) == len(rules["data"])

    add = twitter2_app.tweets.search.stream.rules(
        _json={"add": [{"value": '"gaga"'}, {"value": '"bieber"'}]}
    )
    assert "meta" in add and "summary" in add["meta"] and add["meta"]["summary"].get("created", 0) == 2
    assert "data" in add and len(add["data"]) == 2

    # Sometimes Twitter matches tweets with keywords from urls or users
    # which are more complex to check so we allow a few mismatches
    mismatch = 0
    for tweet in twitter2_stream.tweets.search.stream(
        expansions="referenced_tweets.id",
        params={"tweet.fields": "referenced_tweets,text"}
    ):
        assert "data" in tweet and "text" in tweet["data"]
        lowtext = tweet["data"]["text"].lower()
        if "gaga" in lowtext or "bieber" in lowtext:
            break
        mismatch += 1
        if mismatch > 5:
            assert "gaga" in lowtext or "bieber" in lowtext


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

    p = pickle.dumps(twitter11)
    s = pickle.loads(p)
    assert twitter11.domain == s.domain


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
