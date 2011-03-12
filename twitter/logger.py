"""
tw-archiver - Twitter Archiver

USAGE:

    tw-archiver [OPTIONS]

DESCRIPTION:

    Produce a complete archive in text form of a user's tweets. The
    archive format is:

        screen_name tweet_id tweet_time

            Tweet text spanning multiple lines with
            each line indented by four spaces.

    Each tweet is separated by a blank line.

"""

import sys
import os
from time import sleep


OPTIONS = {
    'oauth_filename': os.environ.get('HOME', '') + os.sep + '.twitter_oauth',
}

from api import Twitter, TwitterError
from cmdline import CONSUMER_KEY, CONSUMER_SECRET
from oauth import read_token_file, OAuth

def log_debug(msg):
    print >> sys.stderr, msg

def get_tweets(twitter, max_id=None):
    kwargs = dict(count=3200)
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
        for line in tweet['text'].splitlines():
            print '    ' + line.encode('utf-8')
        print
        max_id = tweet['id']
        n_tweets += 1
    return n_tweets, max_id

def main(args=sys.argv[1:]):
    oauth_filename = OPTIONS['oauth_filename']
    oauth_token, oauth_token_secret = read_token_file(oauth_filename)

    twitter = Twitter(
        auth=OAuth(
            oauth_token, oauth_token_secret, CONSUMER_KEY, CONSUMER_SECRET),
        api_version='1',
        domain='api.twitter.com')

    if args:
        max_id = args[0]
    else:
        max_id = None

    n_tweets = 0
    while True:
        try:
            tweets_processed, max_id = get_tweets(twitter, max_id)
            n_tweets += tweets_processed
            log_debug("Processed %i tweets (max_id %s)" %(n_tweets, max_id))
            if tweets_processed == 0:
                log_debug("That's it, we got all the tweets. Done.")
                break
        except TwitterError, e:
            log_debug("Twitter bailed out. I'm going to sleep a bit then try again")
            sleep(3)
