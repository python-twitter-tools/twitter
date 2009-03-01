"""
USAGE:

 twitter [action] [options]

ACTIONS:
 follow         add the specified user to your follow list
 friends        get latest tweets from your friends (default action)
 help           print this help text that you are currently reading
 leave          remove the specified user from your following list
 public         get latest public tweets
 replies        get latest replies
 set            set your twitter status

OPTIONS:

 -e --email <email>         your email to login to twitter
 -p --password <password>   your twitter password
 -r --refresh               run this command forever, polling every once
                            in a while (default: every 5 minutes)
 -R --refresh-rate <rate>   set the refresh rate (in seconds)
 -f --format <format>       specify the output format for status updates
 -c --config <filename>     read username and password from given config
                              file (default ~/.twitter)

FORMATS for the --format option

 default         one line per status
 verbose         multiple lines per status, more verbose status info
 urls            nothing but URLs
 ansi            ansi colour (rainbow mode)
 
CONFIG FILES

 The config file should contain a [twitter] header, and all the desired options
 you wish to set, like so:

[twitter]
email: <username>
password: <password>
format: <desired_default_format_for_output>
"""

import sys
import time
from getopt import getopt, GetoptError
from getpass import getpass
import re
import os.path
from ConfigParser import SafeConfigParser

from api import Twitter, TwitterError
import ansi

# Please don't change this, it was provided by the fine folks at Twitter.
# If you change it, it will not work.
AGENT_STR = "twittercommandlinetoolpy"

OPTIONS = {
    'email': None,
    'password': None,
    'action': 'friends',
    'refresh': False,
    'refresh_rate': 600,
    'format': 'default',
    'config_filename': os.environ.get('HOME', '') + os.sep + '.twitter',
    'extra_args': []
}

def parse_args(args, options):
    long_opts = ['email', 'password', 'help', 'format', 'refresh',
                 'refresh-rate', 'config']
    short_opts = "e:p:f:h?rR:c:"
    opts, extra_args = getopt(args, short_opts, long_opts)        

    for opt, arg in opts:
        if opt in ('-e', '--email'):
            options['email'] = arg
        elif opt in ('-p', '--password'):
            options['password'] = arg
        elif opt in ('-f', '--format'):
            options['format'] = arg
        elif opt in ('-r', '--refresh'):
            options['refresh'] = True
        elif opt in ('-R', '--refresh-rate'):
            options['refresh_rate'] = int(arg)
        elif opt in ('-?', '-h', '--help'):
            print __doc__
            sys.exit(0)
        elif opt in ('-c', '--config'):
            options['config_filename'] = arg

    if extra_args:
        options['action'] = extra_args[0]
    options['extra_args'] = extra_args[1:]

class StatusFormatter(object):
    def __call__(self, status):
        return (u"%s %s" %(
            status['user']['screen_name'], status['text']))

class AnsiStatusFormatter(object):
    def __init__(self):
        self._colourMap = ansi.ColourMap()
        
    def __call__(self, status):
        colour = self._colourMap.colourFor(status['user']['screen_name'])
        return (u"%s%s%s %s" %(
            ansi.cmdColour(colour), status['user']['screen_name'],
            ansi.cmdReset(), status['text']))    
    
class VerboseStatusFormatter(object):
    def __call__(self, status):
        return (u"-- %s (%s) on %s\n%s\n" %(
            status['user']['screen_name'],
            status['user']['location'],
            status['created_at'],
            status['text']))

class URLStatusFormatter(object):
    urlmatch = re.compile(r'https?://\S+')
    def __call__(self, status):
        urls = self.urlmatch.findall(status['text'])
        return u'\n'.join(urls) if urls else ""

class AdminFormatter(object):
    def __call__(self, action, user):
        user_str = u"%s (%s)" %(user['screen_name'], user['name'])
        if action == "follow":
            return u"You are now following %s.\n" %(user_str)
        else:
            return u"You are no longer following %s.\n" %(user_str)

class VerboseAdminFormatter(object):
    def __call__(self, action, user):
        return(u"-- %s: %s (%s): %s" % (
            "Following" if action == "follow" else "Leaving", 
            user['screen_name'], 
            user['name'],
            user['url']))

status_formatters = {
    'default': StatusFormatter,
    'verbose': VerboseStatusFormatter,
    'urls': URLStatusFormatter,
    'ansi': AnsiStatusFormatter
}    

admin_formatters = {
    'default': AdminFormatter,
    'verbose': VerboseAdminFormatter,
    'urls': AdminFormatter,
    'ansi': AdminFormatter
}

def get_status_formatter(options):
    sf = status_formatters.get(options['format'])
    if (not sf):
        raise TwitterError(
            "Unknown formatter '%s'" %(options['format']))
    return sf()

def get_admin_formatter(options):
    sf = admin_formatters.get(options['format'])
    if (not sf):
        raise TwitterError(
            "Unknown formatter '%s'" %(options['format']))
    return sf()

class Action(object):
    pass

class NoSuchAction(Action):
    def __call__(self, twitter, options):
        print >> sys.stderr, "No such action: ", options['action']
        sys.exit(1)

class StatusAction(Action):
    def __call__(self, twitter, options):
        statuses = self.getStatuses(twitter)
        sf = get_status_formatter(options)
        for status in statuses:
            statusStr = sf(status)
            if statusStr.strip():
                print statusStr.encode(sys.stdout.encoding, 'replace')

class AdminAction(Action):
    def __call__(self, twitter, options):
        if not options['extra_args'][0]:
            raise TwitterError("You need to specify a user (screen name)")
        af = get_admin_formatter(options)
        try:
            user = self.getUser(twitter, options['extra_args'][0])
        except TwitterError, e:
            print "There was a problem following or leaving the specified user."
            print "  You may be trying to follow a user you are already following;"
            print "  Leaving a user you are not currently following;"
            print "  Or the user may not exist."
            print "  Sorry."
            print
            print e
        else:
            print af(options['action'], user).encode(sys.stdout.encoding, 'replace')

class FriendsAction(StatusAction):
    def getStatuses(self, twitter):
        return reversed(twitter.statuses.friends_timeline())

class PublicAction(StatusAction):
    def getStatuses(self, twitter):
        return reversed(twitter.statuses.public_timeline())

class RepliesAction(StatusAction):
    def getStatuses(self, twitter):
        return reversed(twitter.statuses.replies())

class FollowAction(AdminAction):
    def getUser(self, twitter, user):
        return twitter.notifications.follow(id=user)

class LeaveAction(AdminAction):
    def getUser(self, twitter, user):
        return twitter.notifications.leave(id=user)

class SetStatusAction(Action):
    def __call__(self, twitter, options):
        statusTxt = (u" ".join(options['extra_args']) 
                     if options['extra_args'] 
                     else unicode(raw_input("message: ")))
        status = (statusTxt.encode('utf8', 'replace'))
        twitter.statuses.update(status=status)

class HelpAction(Action):
    def __call__(self, twitter, options):
        print __doc__

actions = {
    'follow': FollowAction,
    'friends': FriendsAction,
    'help': HelpAction,
    'leave': LeaveAction,
    'public': PublicAction,
    'replies': RepliesAction,
    'set': SetStatusAction,
}

def loadConfig(filename):
    options = dict(OPTIONS)
    if os.path.exists(filename):
        cp = SafeConfigParser()
        cp.read([filename])
        for option in ('email', 'password', 'format'):
            if cp.has_option('twitter', option):
                options[option] = cp.get('twitter', option)
    return options

def main(args=sys.argv[1:]):
    arg_options = {}
    try:
        parse_args(args, arg_options)
    except GetoptError, e:
        print >> sys.stderr, "I can't do that, %s." %(e)
        print >> sys.stderr
        sys.exit(1)

    config_options = loadConfig(
        arg_options.get('config_filename') or OPTIONS.get('config_filename'))

    # Apply the various options in order, the most important applied last.
    # Defaults first, then what's read from config file, then command-line
    # arguments.
    options = dict(OPTIONS)
    for d in config_options, arg_options:
        for k,v in d.items():
            if v: options[k] = v
    
    if options['refresh'] and options['action'] not in (
        'friends', 'public', 'replies'):
        print >> sys.stderr, "You can only refresh the friends, public, or replies actions."
        print >> sys.stderr, "Use 'twitter -h' for help."
        sys.exit(1)
        
    if options['email'] and not options['password']:
        options['password'] = getpass("Twitter password: ")
        
    twitter = Twitter(options['email'], options['password'], agent=AGENT_STR)
    action = actions.get(options['action'], NoSuchAction)()
    
    try:
        doAction = lambda : action(twitter, options)

        if (options['refresh'] and isinstance(action, StatusAction)):
            while True:
                doAction()
                time.sleep(options['refresh_rate'])
        else:
            doAction()

    except TwitterError, e:
        print >> sys.stderr, e.args[0]
        print >> sys.stderr, "Use 'twitter -h' for help."
        sys.exit(1)
    except KeyboardInterrupt:
        pass

