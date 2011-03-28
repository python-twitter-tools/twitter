"""
Example program for the Stream API. This prints public status messages
from the "sample" stream as fast as possible.

USAGE

  twitter-stream-example <username> <password>

"""

from __future__ import print_function

import sys

from .stream import TwitterStream
from .auth import UserPassAuth
from .util import printNicely

def main(args=sys.argv[1:]):
    if not args[1:]:
        print(__doc__)
        return 1

    # When using twitter stream you must authorize. UserPass or OAuth.
    stream = TwitterStream(auth=UserPassAuth(args[0], args[1]))

    # Iterate over the sample stream.
    tweet_iter = stream.statuses.sample()
    for tweet in tweet_iter:
        # You must test that your tweet has text. It might be a delete
        # or data message.
        if tweet.get('text'):
            printNicely(tweet['text'])
