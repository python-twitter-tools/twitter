"""
twitter-log - Twitter Logger/Archiver

USAGE:

    twitter-log <screen_name> [max_id]

DESCRIPTION:

    Produce a complete archive in text form of a user's tweets. The
    archive format is:

        screen_name tweet_id tweet_time

            Tweet text possibly spanning multiple lines with
            each line indented by four spaces.

    Each tweet is separated by a blank line.

"""

import sys
import os
from time import sleep

from api import Twitter, TwitterError
from cmdline import CONSUMER_KEY, CONSUMER_SECRET
from auth import NoAuth

def log_debug(msg):
    print >> sys.stderr, msg

def get_tweets(twitter, screen_name, max_id=None):
    kwargs = dict(count=3200, screen_name=screen_name)
    if max_id:
        kwargs['max_id'] = max_id

    n_tweets = 0
    tweets = twitter.statuses.user_timeline(**kwargs)
    for tweet in tweets:
        if tweet['id'] == max_id:
            continue
        print "%s %s %s" % (tweet['user']['screen_name'],
                            tweet['id'],
                            tweet['created_at'])
        print
        for line in tweet['text'].splitlines():
            print '    ' + line.encode('utf-8')
        print
        max_id = tweet['id']
        n_tweets += 1
    return n_tweets, max_id

def main(args=sys.argv[1:]):
    twitter = Twitter(
        auth=NoAuth(),
        api_version='1',
        domain='api.twitter.com')

    if not args:
        print __doc__
        return 1

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
                log_debug("That's it, we got all the tweets. Done.")
                break
        except TwitterError, e:
            log_debug("Twitter bailed out. I'm going to sleep a bit then try again")
            sleep(3)

    return 0
