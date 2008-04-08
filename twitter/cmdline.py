"""
USAGE:

 twitter [action] [options]

ACTIONS:

 friends        get latest tweets from your friends (default action)
 public         get latest public tweets
 set            set your twitter status

OPTIONS:

 -e --email <email>         your email to login to twitter
 -p --password <password>   your twitter password
"""

import sys
from getopt import getopt

from api import Twitter, TwitterError

options = {
    'email': None,
    'password': None,
    'action': 'friends',
    'forever': False,
    'refresh': 600,
    'extra_args': []
}

def parse_args(args, options):
    long_opts = ['email', 'password', 'help']
    short_opts = "e:p:h?"
    opts, extra_args = getopt(args, short_opts, long_opts)
    
    for opt, arg in opts:
        if opt in ('-e', '--email'):
            options['email'] = arg
        elif opt in ('-p', '--password'):
            options['password'] = arg
        elif opt in ('-?', '-h', '--help'):
            print __doc__
            sys.exit(0)
    
    if extra_args:
        options['action'] = extra_args[0]
    options['extra_args'] = extra_args[1:]

class StatusFormatter(object):
    def __call__(self, status):
        return (u"%s: %s" %(
            status['user']['screen_name'], status['text'])).encode(
                sys.stdout.encoding, 'replace')

def no_action(twitter, options):
    print >> sys.stderr, "No such action: ", options['action']
    sys.exit(1)
    
def action_friends(twitter, options):
    statuses = reversed(twitter.statuses.friends_timeline())
    sf = StatusFormatter()
    for status in statuses:
        print sf(status)

def action_public(twitter, options):
    statuses = reversed(twitter.statuses.public_timeline())
    sf = StatusFormatter()
    for status in statuses:
        print sf(status)

def action_set_status(twitter, options):
    twitter.statuses.update(
        status=(u" ".join(options['extra_args'])).encode(
            'utf8', 'replace'))

actions = {
    'friends': action_friends,
    'public': action_public,
    'set': action_set_status,
}


def main():
    return main_with_args(sys.argv[1:])
    
def main_with_args(args):
    parse_args(args, options)
    twitter = Twitter(options['email'], options['password'])
    action = actions.get(options['action'], no_action)
    try:
        action(twitter, options)
    except TwitterError, e:
        print >> sys.stderr, e.message
        print >> sys.stderr, "Use 'twitter -h' for help."
        sys.exit(1)
