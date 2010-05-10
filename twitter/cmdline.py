"""
USAGE:

 twitter [action] [options]


ACTIONS:
 authorize      authorize the command-line tool to interact with Twitter
 follow         add the specified user to your follow list
 friends        get latest tweets from your friends (default action)
 help           print this help text that you are currently reading
 leave          remove the specified user from your following list
 public         get latest public tweets
 replies        get latest replies
 search         search twitter (Beware: octothorpe, escape it)
 set            set your twitter status
 shell          login the twitter shell


OPTIONS:

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
    --no-ssl                use HTTP instead of more secure HTTPS
    --oauth <filename>      filename to read/store oauth credentials to

FORMATS for the --format option

 default         one line per status
 verbose         multiple lines per status, more verbose status info
 urls            nothing but URLs
 ansi            ansi colour (rainbow mode)


CONFIG FILES

 The config file should be placed in your home directory and be named .twitter.
 It must contain a [twitter] header, and all the desired options you wish to
 set, like so:

[twitter]
format: <desired_default_format_for_output>
prompt: <twitter_shell_prompt e.g. '[cyan]twitter[R]> '>

 OAuth authentication tokens are stored in the file .twitter_oauth in your
 home directory.
"""

CONSUMER_KEY='uS6hO2sV6tDKIOeVjhnFnQ'
CONSUMER_SECRET='MEYTOS97VvlHX7K1rwHPEqVpTSqZ71HtvoK4sVuYk'

import sys
import time
from getopt import gnu_getopt as getopt, GetoptError
from getpass import getpass
import re
import os.path
from ConfigParser import SafeConfigParser
import datetime
from urllib import quote
import webbrowser

from api import Twitter, TwitterError
from oauth import OAuth
import ansi

OPTIONS = {
    'action': 'friends',
    'refresh': False,
    'refresh_rate': 600,
    'format': 'default',
    'prompt': '[cyan]twitter[R]> ',
    'config_filename': os.environ.get('HOME', '') + os.sep + '.twitter',
    'oauth_filename': os.environ.get('HOME', '') + os.sep + '.twitter_oauth',
    'length': 20,
    'timestamp': False,
    'datestamp': False,
    'extra_args': [],
    'secure': True,
}

def parse_args(args, options):
    long_opts = ['help', 'format=', 'refresh', 'oauth=',
                 'refresh-rate=', 'config=', 'length=', 'timestamp', 
                 'datestamp', 'no-ssl']
    short_opts = "e:p:f:h?rR:c:l:td"
    opts, extra_args = getopt(args, short_opts, long_opts)        

    for opt, arg in opts:
        if opt in ('-f', '--format'):
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
        elif opt == '--no-ssl':
            options['secure'] = False
        elif opt == '--oauth':
            options['oauth_filename'] = arg

    if extra_args and not ('action' in options and options['action'] == 'help'):
        options['action'] = extra_args[0]
    options['extra_args'] = extra_args[1:]

def get_time_string(status, options, format="%a %b %d %H:%M:%S +0000 %Y"):
    timestamp = options["timestamp"]
    datestamp = options["datestamp"]
    t = time.strptime(status['created_at'], format)
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

class SearchFormatter(object):
    def __call__(self, result, options):
        return(u"%s%s %s" %(
            get_time_string(result, options, "%a, %d %b %Y %H:%M:%S +0000"),
            result['from_user'], result['text']))

class VerboseSearchFormatter(SearchFormatter):
    pass #Default to the regular one

class URLSearchFormatter(object):
    urlmatch = re.compile(r'https?://\S+')
    def __call__(self, result, options):
        urls = self.urlmatch.findall(result['text'])
        return u'\n'.join(urls) if urls else ""

class AnsiSearchFormatter(object):
    def __init__(self):
        self._colourMap = ansi.ColourMap()

    def __call__(self, result, options):
        colour = self._colourMap.colourFor(result['from_user'])
        return (u"%s%s%s%s %s" %(
            get_time_string(result, options, "%a, %d %b %Y %H:%M:%S +0000"),
            ansi.cmdColour(colour), result['from_user'],
            ansi.cmdReset(), result['text']))

formatters = {}
status_formatters = {
    'default': StatusFormatter,
    'verbose': VerboseStatusFormatter,
    'urls': URLStatusFormatter,
    'ansi': AnsiStatusFormatter
}
formatters['status'] = status_formatters

admin_formatters = {
    'default': AdminFormatter,
    'verbose': VerboseAdminFormatter,
    'urls': AdminFormatter,
    'ansi': AdminFormatter
}
formatters['admin'] = admin_formatters

search_formatters = {
    'default': SearchFormatter,
    'verbose': VerboseSearchFormatter,
    'urls': URLSearchFormatter,
    'ansi': AnsiSearchFormatter
}
formatters['search'] = search_formatters

def get_formatter(action_type, options):
    formatters_dict = formatters.get(action_type)
    if (not formatters_dict):
        raise TwitterError(
            "There was an error finding a class of formatters for your type (%s)"
            %(action_type))
    f = formatters_dict.get(options['format'])
    if (not f):
        raise TwitterError(
            "Unknown formatter '%s' for status actions" %(options['format']))
    return f()

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
        sf = get_formatter('status', options)
        for status in statuses:
            statusStr = sf(status, options)
            if statusStr.strip():
                printNicely(statusStr)

class SearchAction(Action):
    def __call__(self, twitter, options):
        # We need to be pointing at search.twitter.com to work, and it is less
        # tangly to do it here than in the main()
        twitter.domain="search.twitter.com"
        twitter.uri=""
        # We need to bypass the TwitterCall parameter encoding, so we
        # don't encode the plus sign, so we have to encode it ourselves
        query_string = "+".join([quote(term) for term in options['extra_args']])
        twitter.encoded_args = "q=%s" %(query_string)

        results = twitter.search()['results']
        f = get_formatter('search', options)
        for result in results:
            resultStr = f(result, options)
            if resultStr.strip():
                printNicely(resultStr)

class AdminAction(Action):
    def __call__(self, twitter, options):
        if not (options['extra_args'] and options['extra_args'][0]):
            raise TwitterError("You need to specify a user (screen name)")
        af = get_formatter('admin', options)
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

class DoNothingAction(Action):
    def __call__(self, twitter, options):
        pass

def parse_oauth_tokens(result):
    for r in result.split('&'):
        k, v = r.split('=')
        if k == 'oauth_token':
            oauth_token = v
        elif k == 'oauth_token_secret':
            oauth_token_secret = v
    return oauth_token, oauth_token_secret

def oauth_dance(options):
    print ("Hi there! We're gonna get you all set up to use Twitter"
           " on the command-line.")
    twitter = Twitter(
        auth=OAuth('', '', CONSUMER_KEY, CONSUMER_SECRET),
        format='')
    oauth_token, oauth_token_secret = parse_oauth_tokens(
        twitter.oauth.request_token())
    print """
In the web browser window that opens please choose to Allow access to the
command-line tool. Copy the PIN number that appears on the next page and
paste or type it here:
"""
    webbrowser.open(
        'http://api.twitter.com/oauth/authorize?oauth_token=' +
        oauth_token)
    time.sleep(2) # Sometimes the last command can print some
                  # crap. Wait a bit so it doesn't mess up the next
                  # prompt.
    oauth_verifier = raw_input("Please type the PIN: ").strip()
    twitter = Twitter(
        auth=OAuth(
            oauth_token, oauth_token_secret, CONSUMER_KEY, CONSUMER_SECRET),
        format='')
    oauth_token, oauth_token_secret = parse_oauth_tokens(
        twitter.oauth.access_token(oauth_verifier=oauth_verifier))
    oauth_file = open(options['oauth_filename'], 'w')
    print >> oauth_file, oauth_token
    print >> oauth_file, oauth_token_secret
    oauth_file.close()
    print
    print "That's it! Your authorization keys have been written to %s." % (
        options['oauth_filename'])


actions = {
    'authorize' : DoNothingAction,
    'follow'    : FollowAction,
    'friends'   : FriendsAction,
    'help'      : HelpAction,
    'leave'     : LeaveAction,
    'public'    : PublicAction,
    'replies'   : RepliesAction,
    'search'    : SearchAction,
    'set'       : SetStatusAction,
    'shell'     : TwitterShell,
}

def loadConfig(filename):
    options = dict(OPTIONS)
    if os.path.exists(filename):
        cp = SafeConfigParser()
        cp.read([filename])
        for option in ('format', 'prompt'):
            if cp.has_option('twitter', option):
                options[option] = cp.get('twitter', option)
    return options

def read_oauth_file(fn):
    f = open(fn)
    return f.readline().strip(), f.readline().strip()

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
        return 1

    if (options['action'] == 'authorize'
        or not os.path.exists(options['oauth_filename'])):
        oauth_dance(options)

    oauth_token, oauth_token_secret = read_oauth_file(options['oauth_filename'])
    
    twitter = Twitter(
        auth=OAuth(
            oauth_token, oauth_token_secret, CONSUMER_KEY, CONSUMER_SECRET),
        secure=options['secure'],
        api_version='1')

    try:
        Action()(twitter, options)
    except NoSuchActionError, e:
        print >>sys.stderr, e
        raise SystemExit(1)
    except TwitterError, e:
        print >> sys.stderr, e.args[0]
        print >> sys.stderr, "Use 'twitter -h' for help."
        raise SystemExit(1)
