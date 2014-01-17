"""
Example program for the Stream API. This prints public status messages
from the "sample" stream as fast as possible.

USAGE

  stream-example -t <token> -ts <token_secret> -ck <consumer_key> -cs <consumer_secret>

"""

from __future__ import print_function

import argparse

from twitter.stream import TwitterStream
from twitter.oauth import OAuth
from twitter.util import printNicely


def parse_arguments():

    parser = argparse.ArgumentParser()

    parser.add_argument('-t',  '--token', help='The Twitter Access Token.')
    parser.add_argument('-ts', '--token_secret', help='The Twitter Access Token Secret.')
    parser.add_argument('-ck', '--consumer_key', help='The Twitter Consumer Key.')
    parser.add_argument('-cs', '--consumer_secret', help='The Twitter Consumer Secret.')

    return parser.parse_args()

##  parse_arguments()


def main():

    args = parse_arguments()

    # When using twitter stream you must authorize.
    stream = TwitterStream(auth=OAuth(args.token, args.token_secret, args.consumer_key, args.consumer_secret))

    # Iterate over the sample stream.
    tweet_iter = stream.statuses.sample()
    for tweet in tweet_iter:
        # You must test that your tweet has text. It might be a delete
        # or data message.
        if tweet.get('text'):
            printNicely(tweet['text'])

##  main()

if __name__ == '__main__':
    main()
