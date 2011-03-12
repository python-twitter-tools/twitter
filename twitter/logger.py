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

OPTIONS = {
    'oauth_filename': os.environ.get('HOME', '') + os.sep + '.twitter_oauth',
}

from api import Twitter
from cmdline import CONSUMER_KEY, CONSUMER_SECRET
from oauth import read_token_file, OAuth

def main(args=sys.argv[1:]):
    oauth_filename = OPTIONS['oauth_filename']
    oauth_token, oauth_token_secret = read_token_file(oauth_filename)

    twitter = Twitter(
        auth=OAuth(
            oauth_token, oauth_token_secret, CONSUMER_KEY, CONSUMER_SECRET),
        api_version='1',
        domain='api.twitter.com')

    kwargs = dict(count=3200)

    tweets = twitter.statuses.user_timeline(**kwargs)
    for tweet in tweets:
        print "%s %s %s" % (tweet['user']['screen_name'],
                            tweet['id'],
                            tweet['created_at'])
        for line in tweet['text'].splitlines():
            print '    ' + line.encode('utf-8')
        print
