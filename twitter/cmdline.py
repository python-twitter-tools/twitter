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
 shell          login the twitter shell

OPTIONS:

 -e --email <email>         your email to login to twitter
 -p --password <password>   your twitter password
 -r --refresh               run this command forever, polling every once
                            in a while (default: every 5 minutes)
 -R --refresh-rate <rate>   set the refresh rate (in seconds)
 -f --format <format>       specify the output format for status updates
 -c --config <filename>     read username and password from given config
                            file (default ~/.twitter)
 -l --length <count>        specify number of status updates shown
                            (default: 20, max: 200)
 -t --timestamp             show time before status lines
 -d --datestamp             shoe date before status lines

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
prompt: <twitter_shell_prompt e.g. '[cyan]twitter[R]> '>
"""

import sys
import time
from getopt import gnu_getopt as getopt, GetoptError
from getpass import getpass
import re
import os.path
from ConfigParser import SafeConfigParser
import datetime

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
    'prompt': '[cyan]twitter[R]> ',
    'config_filename': os.environ.get('HOME', '') + os.sep + '.twitter',
    'length': 20,
    'timestamp': False,
    'datestamp': False,
    'extra_args': []
}

def parse_args(args, options):
    long_opts = ['email', 'password', 'help', 'format', 'refresh',
                 'refresh-rate', 'config', 'length', 'timestamp', 'datestamp']
    short_opts = "e:p:f:h?rR:c:l:td"
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
        elif opt in ('-l', '--length'):
            options["length"] = int(arg)
        elif opt in ('-t', '--timestamp'):
            options["timestamp"] = True
        elif opt in ('-d', '--datestamp'):
            options["datestamp"] = True
        elif opt in ('-?', '-h', '--help'):
            options['action'] = 'help'
        elif opt in ('-c', '--config'):
            options['config_filename'] = arg

    if extra_args and not ('action' in options and options['action'] == 'help'):
        options['action'] = extra_args[0]
    options['extra_args'] = extra_args[1:]
    
def get_time_string(status, options):
    timestamp = options["timestamp"]
    datestamp = options["datestamp"]
    t = time.strptime(status['created_at'], "%a %b %d %H:%M:%S +0000 %Y")
    i_hate_timezones = time.timezone
    if (time.daylight):
        i_hate_timezones = time.altzone
    dt = datetime.datetime(*t[:-3]) - datetime.timedelta(
        seconds=i_hate_timezones)
    t = dt.timetuple()
    if timestamp and datestamp:
        return time.strftime("%Y-%m-%d %H:%M:%S ", t)
    elif timestamp:
        return time.strftime("%H:%M:%S ", t)
    elif datestamp:
        return time.strftime("%Y-%m-%d ", t)
    return ""                             

class StatusFormatter(object):
    def __call__(self, status, options):
        return (u"%s%s %s" %(
            get_time_string(status, options),
            status['user']['screen_name'], status['text']))

class AnsiStatusFormatter(object):
    def __init__(self):
        self._colourMap = ansi.ColourMap()
        
    def __call__(self, status, options):
        colour = self._colourMap.colourFor(status['user']['screen_name'])
        return (u"%s%s%s%s %s" %(
            get_time_string(status, options),
            ansi.cmdColour(colour), status['user']['screen_name'],
            ansi.cmdReset(), status['text']))

class VerboseStatusFormatter(object):
    def __call__(self, status, options):
        return (u"-- %s (%s) on %s\n%s\n" %(
            status['user']['screen_name'],
            status['user']['location'],
            status['created_at'],
            status['text']))

class URLStatusFormatter(object):
    urlmatch = re.compile(r'https?://\S+')
    def __call__(self, status, options):
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

    def ask(self, subject='perform this action', careful=False):
        '''
        Requests fromt he user using `raw_input` if `subject` should be
        performed. When `careful`, the default answer is NO, otherwise YES.
        Returns the user answer in the form `True` or `False`.
        '''
        sample = '(y/N)'
        if not careful:
            sample = '(Y/n)'
        
        prompt = 'You really want to %s %s? ' %(subject, sample)
        try:
            answer = raw_input(prompt).lower()
            if careful:
                return answer in ('yes', 'y')
            else:
                return answer not in ('no', 'n')
        except EOFError:
            print >>sys.stderr # Put Newline since Enter was never pressed
            # TODO:
                #   Figure out why on OS X the raw_input keeps raising
                #   EOFError and is never able to reset and get more input
                #   Hint: Look at how IPython implements their console
            default = True
            if careful:
                default = False
            return default
        
    def __call__(self, twitter, options):
        action = actions.get(options['action'], NoSuchAction)()
        try:
            doAction = lambda : action(twitter, options)
            if (options['refresh'] and isinstance(action, StatusAction)):
                while True:
                    doAction()
                    time.sleep(options['refresh_rate'])
            else:
                doAction()
        except KeyboardInterrupt:
            print >>sys.stderr, '\n[Keyboard Interrupt]'
            pass

class NoSuchActionError(Exception):
    pass

class NoSuchAction(Action):
    def __call__(self, twitter, options):
        raise NoSuchActionError("No such action: %s" %(options['action']))

def printNicely(string):        
    if sys.stdout.encoding:
        print string.encode(sys.stdout.encoding, 'replace')
    else:
        print string.encode('utf-8')
        
class StatusAction(Action):
    def __call__(self, twitter, options):
        statuses = self.getStatuses(twitter, options)
        sf = get_status_formatter(options)
        for status in statuses:
            statusStr = sf(status, options)
            if statusStr.strip():
                printNicely(statusStr)

class AdminAction(Action):
    def __call__(self, twitter, options):
        if not (options['extra_args'] and options['extra_args'][0]):
            raise TwitterError("You need to specify a user (screen name)")
        af = get_admin_formatter(options)
        try:
            user = self.getUser(twitter, options['extra_args'][0])
        except TwitterError, e:
            print "There was a problem following or leaving the specified user."
            print "You may be trying to follow a user you are already following;"
            print "Leaving a user you are not currently following;"
            print "Or the user may not exist."
            print "Sorry."
            print
            print e
        else:
            printNicely(af(options['action'], user))

class FriendsAction(StatusAction):
    def getStatuses(self, twitter, options):
        return reversed(twitter.statuses.friends_timeline(count=options["length"]))

class PublicAction(StatusAction):
    def getStatuses(self, twitter, options):
        return reversed(twitter.statuses.public_timeline(count=options["length"]))

class RepliesAction(StatusAction):
    def getStatuses(self, twitter, options):
        return reversed(twitter.statuses.replies(count=options["length"]))

class FollowAction(AdminAction):
    def getUser(self, twitter, user):
        return twitter.friendships.create(id=user)

class LeaveAction(AdminAction):
    def getUser(self, twitter, user):
        return twitter.friendships.destroy(id=user)

class SetStatusAction(Action):
    def __call__(self, twitter, options):
        statusTxt = (u" ".join(options['extra_args'])
                     if options['extra_args']
                     else unicode(raw_input("message: ")))
        status = (statusTxt.encode('utf8', 'replace'))
        twitter.statuses.update(status=status)

class TwitterShell(Action):

    def render_prompt(self, prompt):
        '''Parses the `prompt` string and returns the rendered version'''
        prompt = prompt.strip("'").replace("\\'","'")
        for colour in ansi.COLOURS_NAMED:
            if '[%s]' %(colour) in prompt:
                prompt = prompt.replace(
                            '[%s]' %(colour), ansi.cmdColourNamed(colour))
        prompt = prompt.replace('[R]', ansi.cmdReset())
        return prompt
    
    def __call__(self, twitter, options):
        prompt = self.render_prompt(options.get('prompt', 'twitter> '))
        while True:
            options['action'] = ""
            try:
                args = raw_input(prompt).split()
                parse_args(args, options)
                if not options['action']:
                    continue
                elif options['action'] == 'exit':
                    raise SystemExit(0)
                elif options['action'] == 'shell':
                    print >>sys.stderr, 'Sorry Xzibit does not work here!'
                    continue
                elif options['action'] == 'help':
                    print >>sys.stderr, '''\ntwitter> `action`\n
        The Shell Accepts all the command line actions along with:

            exit    Leave the twitter shell (^D may also be used)

        Full CMD Line help is appended below for your convinience.'''
                Action()(twitter, options)
                options['action'] = ''
            except NoSuchActionError, e:
                print >>sys.stderr, e
            except KeyboardInterrupt:
                print >>sys.stderr, '\n[Keyboard Interrupt]'
            except EOFError:
                print >>sys.stderr
                leaving = self.ask(subject='Leave')
                if not leaving:
                    print >>sys.stderr, 'Excellent!'
                else:
                    raise SystemExit(0)

class HelpAction(Action):
    def __call__(self, twitter, options):
        print __doc__

actions = {
    'follow'    : FollowAction,
    'friends'   : FriendsAction,
    'help'      : HelpAction,
    'leave'     : LeaveAction,
    'public'    : PublicAction,
    'replies'   : RepliesAction,
    'set'       : SetStatusAction,
    'shell'     : TwitterShell,
}

def loadConfig(filename):
    options = dict(OPTIONS)
    if os.path.exists(filename):
        cp = SafeConfigParser()
        cp.read([filename])
        for option in ('email', 'password', 'format', 'prompt'):
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
        raise SystemExit(1)

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
        raise SystemExit(1)

    if options['email'] and not options['password']:
        options['password'] = getpass("Twitter password: ")

    twitter = Twitter(options['email'], options['password'], agent=AGENT_STR)
    try:
        Action()(twitter, options)
    except NoSuchActionError, e:
        print >>sys.stderr, e
        raise SystemExit(1)
    except TwitterError, e:
        print >> sys.stderr, e.args[0]
        print >> sys.stderr, "Use 'twitter -h' for help."
        raise SystemExit(1)
