"""USAGE
    twitter-follow [options] <user>

DESCRIPTION
    Display all following/followers of a user, one user per line.

OPTIONS
 -o --oauth            authenticate to Twitter using OAuth (default no)
 -r --followers        display followers of the given user (default)
 -g --following        display users the given user is following
 -a --api-rate         see your current API rate limit status
 -i --ids              prepend user id to each line. useful to tracking renames

AUTHENTICATION
    Authenticate to Twitter using OAuth to see following/followers of private
    profiles and have higher API rate limits. OAuth authentication tokens
    are stored in the file .twitter-follow_oauth in your home directory.
"""

from __future__ import print_function

import os, sys, time, calendar
from getopt import gnu_getopt as getopt, GetoptError

try:
    import urllib.request as urllib2
    import http.client as httplib
except ImportError:
    import urllib2
    import httplib

# T-Follow (Twitter-Follow) application registered by @stalkr_
CONSUMER_KEY='USRZQfvFFjB6UvZIN2Edww'
CONSUMER_SECRET='AwGAaSzZa5r0TDL8RKCDtffnI9H9mooZUdOa95nw8'

from .api import Twitter, TwitterError
from .oauth import OAuth, read_token_file
from .oauth_dance import oauth_dance
from .auth import NoAuth
from .util import Fail, err


def parse_args(args, options):
    """Parse arguments from command-line to set options."""
    long_opts = ['help', 'oauth', 'followers', 'following', 'api-rate', 'ids']
    short_opts = "horgai"
    opts, extra_args = getopt(args, short_opts, long_opts)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print(__doc__)
            raise SystemExit(1)
        elif opt in ('-o', '--oauth'):
            options['oauth'] = True
        elif opt in ('-r', '--followers'):
            options['followers'] = True
        elif opt in ('-g', '--following'):
            options['followers'] = False
        elif opt in ('-a', '--api-rate'):
            options['api-rate' ] = True
        elif opt in ('-i', '--ids'):
            options['show_id'] = True

    options['extra_args'] = extra_args

def lookup_portion(twitter, user_ids):
    """Resolve a limited list of user ids to screen names."""
    users = {}
    kwargs = dict(user_id=",".join(map(str, user_ids)), skip_status=1)
    for u in twitter.users.lookup(**kwargs):
        users[int(u['id'])] = u['screen_name']
    return users

def lookup(twitter, user_ids):
    """Resolve an entire list of user ids to screen names."""
    users = {}
    api_limit = 100
    for i in range(0, len(user_ids), api_limit):
        fail = Fail()
        while True:
            try:
                portion = lookup_portion(twitter, user_ids[i:][:api_limit])
            except TwitterError as e:
                if e.e.code == 429:
                    err("Fail: %i API rate limit exceeded" % e.e.code)
                    rls = twitter.application.rate_limit_status()
                    reset = rls.rate_limit_reset
                    reset = time.asctime(time.localtime(reset))
                    delay = int(rls.rate_limit_reset
                                - time.time()) + 5 # avoid race
                    err("Interval limit of %i requests reached, next reset on "
                        "%s: going to sleep for %i secs"
                        % (rls.rate_limit_limit, reset, delay))
                    fail.wait(delay)
                    continue
                elif e.e.code == 502:
                    err("Fail: %i Service currently unavailable, retrying..."
                        % e.e.code)
                else:
                    err("Fail: %s\nRetrying..." % str(e)[:500])
                fail.wait(3)
            except urllib2.URLError as e:
                err("Fail: urllib2.URLError %s - Retrying..." % str(e))
                fail.wait(3)
            except httplib.error as e:
                err("Fail: httplib.error %s - Retrying..." % str(e))
                fail.wait(3)
            except KeyError as e:
                err("Fail: KeyError %s - Retrying..." % str(e))
                fail.wait(3)
            else:
                users.update(portion)
                err("Resolving user ids to screen names: %i/%i"
                    % (len(users), len(user_ids)))
                break
    return users

def follow_portion(twitter, screen_name, cursor=-1, followers=True):
    """Get a portion of followers/following for a user."""
    kwargs = dict(screen_name=screen_name, cursor=cursor)
    if followers:
        t = twitter.followers.ids(**kwargs)
    else: # following
        t = twitter.friends.ids(**kwargs)
    return t['ids'], t['next_cursor']

def follow(twitter, screen_name, followers=True):
    """Get the entire list of followers/following for a user."""
    user_ids = []
    cursor = -1
    fail = Fail()
    while True:
        try:
            portion, cursor = follow_portion(twitter, screen_name, cursor,
                                             followers)
        except TwitterError as e:
            if e.e.code == 401:
                reason = ("follow%s of that user are protected"
                          % ("ers" if followers else "ing"))
                err("Fail: %i Unauthorized (%s)" % (e.e.code, reason))
                break
            elif e.e.code == 429:
                err("Fail: %i API rate limit exceeded" % e.e.code)
                rls = twitter.application.rate_limit_status()
                reset = rls.rate_limit_reset
                reset = time.asctime(time.localtime(reset))
                delay = int(rls.rate_limit_reset
                            - time.time()) + 5 # avoid race
                err("Interval limit of %i requests reached, next reset on %s: "
                    "going to sleep for %i secs" % (rls.rate_limit_limit,
                                                    reset, delay))
                fail.wait(delay)
                continue
            elif e.e.code == 502:
                err("Fail: %i Service currently unavailable, retrying..."
                    % e.e.code)
            else:
                err("Fail: %s\nRetrying..." % str(e)[:500])
            fail.wait(3)
        except urllib2.URLError as e:
            err("Fail: urllib2.URLError %s - Retrying..." % str(e))
            fail.wait(3)
        except httplib.error as e:
            err("Fail: httplib.error %s - Retrying..." % str(e))
            fail.wait(3)
        except KeyError as e:
            err("Fail: KeyError %s - Retrying..." % str(e))
            fail.wait(3)
        else:
            new = -len(user_ids)
            user_ids = list(set(user_ids + portion))
            new += len(user_ids)
            what = "follow%s" % ("ers" if followers else "ing")
            err("Browsing %s %s, new: %i" % (screen_name, what, new))
            if cursor == 0:
                break
            fail = Fail()
    return user_ids


def rate_limit_status(twitter):
    """Print current Twitter API rate limit status."""
    rls = twitter.application.rate_limit_status()
    print("Remaining API requests: %i/%i (interval limit)"
          % (rls.rate_limit_remaining, rls.rate_limit_limit))
    print("Next reset in %is (%s)"
          % (int(rls.rate_limit_reset - time.time()),
             time.asctime(time.localtime(rls.rate_limit_reset))))

def main(args=sys.argv[1:]):
    options = {
        'oauth': False,
        'followers': True,
        'api-rate': False,
        'show_id': False
    }
    try:
        parse_args(args, options)
    except GetoptError as e:
        err("I can't do that, %s." % e)
        raise SystemExit(1)

    # exit if no user or given, except if asking for API rate
    if not options['extra_args'] and not options['api-rate']:
        print(__doc__)
        raise SystemExit(1)

    # authenticate using OAuth, asking for token if necessary
    if options['oauth']:
        oauth_filename = (os.getenv("HOME", "") + os.sep
                          + ".twitter-follow_oauth")
        if not os.path.exists(oauth_filename):
            oauth_dance("Twitter-Follow", CONSUMER_KEY, CONSUMER_SECRET,
                        oauth_filename)
        oauth_token, oauth_token_secret = read_token_file(oauth_filename)
        auth = OAuth(oauth_token, oauth_token_secret, CONSUMER_KEY,
                     CONSUMER_SECRET)
    else:
        auth = NoAuth()

    twitter = Twitter(auth=auth, api_version='1.1', domain='api.twitter.com')

    if options['api-rate']:
        rate_limit_status(twitter)
        return

    # obtain list of followers (or following) for every given user
    for user in options['extra_args']:
        user_ids, users = [], {}
        try:
            user_ids = follow(twitter, user, options['followers'])
            users = lookup(twitter, user_ids)
        except KeyboardInterrupt as e:
            err()
            err("Interrupted.")
            raise SystemExit(1)

        for uid in user_ids:
            if options['show_id']:
              try:
                print(str(uid) + "\t" + users[uid].encode("utf-8"))
              except KeyError:
                pass

            else:
              try:
                print(users[uid].encode("utf-8"))
              except KeyError:
                pass

        # print total on stderr to separate from user list on stdout
        if options['followers']:
            err("Total followers for %s: %i" % (user, len(user_ids)))
        else:
            err("Total users %s is following: %i" % (user, len(user_ids)))
