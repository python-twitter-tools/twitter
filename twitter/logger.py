"""
twitter-log - Twitter Logger/Archiver

USAGE:

    twitter-log <screen_name> [max_id]

DESCRIPTION:

    Produce a complete archive in text form of a user's tweets. The
    archive format is:

        screen_name <tweet_id>
        Date: <tweet_time>
        [In-Reply-To: a_tweet_id]

            Tweet text possibly spanning multiple lines with
            each line indented by four spaces.


    Each tweet is separated by two blank lines.

"""

from __future__ import print_function

import sys
import os
from time import sleep

from .api import Twitter, TwitterError
from .cmdline import CONSUMER_KEY, CONSUMER_SECRET
from .auth import NoAuth
from .oauth import OAuth, write_token_file, read_token_file
from .oauth_dance import oauth_dance
from .util import printNicely

# Registered by @sixohsix
CONSUMER_KEY = "OifqLIQIufeY9znQCkbvg"
CONSUMER_SECRET = "IedFvi0JitR9yaYw9HwcCCEy4KYaLxf4p4rHRqGgX80"
OAUTH_FILENAME = os.environ.get('HOME', os.environ.get('USERPROFILE', '')) + os.sep + '.twitter_log_oauth'

def log_debug(msg):
    print(msg, file=sys.stderr)

def get_tweets(twitter, screen_name, max_id=None):
    kwargs = dict(count=3200, screen_name=screen_name)
    if max_id:
        kwargs['max_id'] = max_id

    n_tweets = 0
    tweets = twitter.statuses.user_timeline(**kwargs)
    for tweet in tweets:
        if tweet['id'] == max_id:
            continue
        print("%s %s\nDate: %s" % (tweet['user']['screen_name'],
                                   tweet['id'],
                                   tweet['created_at']))
        if tweet.get('in_reply_to_status_id'):
            print("In-Reply-To: %s" % tweet['in_reply_to_status_id'])
        print()
        for line in tweet['text'].splitlines():
            printNicely('    ' + line + '\n')
        print()
        print()
        max_id = tweet['id']
        n_tweets += 1
    return n_tweets, max_id

def main(args=sys.argv[1:]):
    if not args:
        print(__doc__)
        return 1

    if not os.path.exists(OAUTH_FILENAME):
        oauth_dance(
            "the Python Twitter Logger", CONSUMER_KEY, CONSUMER_SECRET,
            OAUTH_FILENAME)

    oauth_token, oauth_token_secret = read_token_file(OAUTH_FILENAME)

    twitter = Twitter(
        auth=OAuth(
            oauth_token, oauth_token_secret, CONSUMER_KEY, CONSUMER_SECRET),
        domain='api.twitter.com')

    screen_name = args[0]

    if args[1:]:
        max_id = args[1]
    else:
        max_id = None

    n_tweets = 0
    while True:
        try:
            tweets_processed, max_id = get_tweets(twitter, screen_name, max_id)
            n_tweets += tweets_processed
            log_debug("Processed %i tweets (max_id %s)" %(n_tweets, max_id))
            if tweets_processed == 0:
                log_debug("That's it, we got all the tweets we could. Done.")
                break
        except TwitterError as e:
            log_debug("Twitter bailed out. I'm going to sleep a bit then try again")
            sleep(3)

    return 0
