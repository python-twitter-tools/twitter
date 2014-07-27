# encoding: utf-8
"""
USAGE:

 twitter [action] [options]


ACTIONS:
 authorize      authorize the command-line tool to interact with Twitter
 follow         follow a user
 friends        get latest tweets from your friends (default action)
 help           print this help text that you are currently reading
 leave          stop following a user
 list           get list of a user's lists; give a list name to get
                    tweets from that list
 mylist         get list of your lists; give a list name to get tweets
                    from that list
 pyprompt       start a Python prompt for interacting with the twitter
                    object directly
 replies        get latest replies to you
 search         search twitter (Beware: octothorpe, escape it)
 set            set your twitter status
 shell          login to the twitter shell
 rate           get your current rate limit status (remaining API reqs)


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
 -d --datestamp             show date before status lines
    --no-ssl                use less-secure HTTP instead of HTTPS
    --oauth <filename>      filename to read/store oauth credentials to

FORMATS for the --format option

 default         one line per status
 verbose         multiple lines per status, more verbose status info
 json            raw json data from the api on each line
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

from __future__ import print_function

try:
    input = __builtins__.raw_input
except (AttributeError, KeyError):
    pass


CONSUMER_KEY = 'uS6hO2sV6tDKIOeVjhnFnQ'
CONSUMER_SECRET = 'MEYTOS97VvlHX7K1rwHPEqVpTSqZ71HtvoK4sVuYk'

from getopt import gnu_getopt as getopt, GetoptError
from getpass import getpass
import json
import locale
import os.path
import re
import string
import sys
import time

try:
    from ConfigParser import SafeConfigParser
except ImportError:
    from configparser import ConfigParser as SafeConfigParser
import datetime
try:
    from urllib.parse import quote
except ImportError:
    from urllib2 import quote
try:
    import HTMLParser
except ImportError:
    import html.parser as HTMLParser

import webbrowser

from .api import Twitter, TwitterError
from .oauth import OAuth, write_token_file, read_token_file
from .oauth_dance import oauth_dance
from . import ansi
from .util import smrt_input, printNicely, align_text

OPTIONS = {
    'action': 'friends',
    'refresh': False,
    'refresh_rate': 600,
    'format': 'default',
    'prompt': '[cyan]twitter[R]> ',
    'config_filename': os.environ.get('HOME', os.environ.get('USERPROFILE', '')) + os.sep + '.twitter',
    'oauth_filename': os.environ.get('HOME', os.environ.get('USERPROFILE', '')) + os.sep + '.twitter_oauth',
    'length': 20,
    'timestamp': False,
    'datestamp': False,
    'extra_args': [],
    'secure': True,
    'invert_split': False,
    'force-ansi': False,
}

gHtmlParser = HTMLParser.HTMLParser()
hashtagRe = re.compile(r'(?P<hashtag>#\S+)')
profileRe = re.compile(r'(?P<profile>\@\S+)')
ansiFormatter = ansi.AnsiCmd(False)

def parse_args(args, options):
    long_opts = ['help', 'format=', 'refresh', 'oauth=',
                 'refresh-rate=', 'config=', 'length=', 'timestamp',
                 'datestamp', 'no-ssl', 'force-ansi']
    short_opts = "e:p:f:h?rR:c:l:td"
    opts, extra_args = getopt(args, short_opts, long_opts)
    if extra_args and hasattr(extra_args[0], 'decode'):
        extra_args = [arg.decode(locale.getpreferredencoding())
                      for arg in extra_args]

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
        elif opt == '--force-ansi':
            options['force-ansi'] = True

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

def reRepl(m):
    ansiTypes = {
          'clear':   ansiFormatter.cmdReset(),
          'hashtag': ansiFormatter.cmdBold(),
          'profile': ansiFormatter.cmdUnderline(),
          }

    s = None
    try:
        mkey = m.lastgroup
        if m.group(mkey):
            s = '%s%s%s' % (ansiTypes[mkey], m.group(mkey), ansiTypes['clear'])
    except IndexError:
        pass
    return s

def replaceInStatus(status):
    txt = gHtmlParser.unescape(status)
    txt = re.sub(hashtagRe, reRepl, txt)
    txt = re.sub(profileRe, reRepl, txt)
    return txt

class StatusFormatter(object):
    def __call__(self, status, options):
        return ("%s%s %s" % (
            get_time_string(status, options),
            status['user']['screen_name'], gHtmlParser.unescape(status['text'])))

class AnsiStatusFormatter(object):
    def __init__(self):
        self._colourMap = ansi.ColourMap()

    def __call__(self, status, options):
        colour = self._colourMap.colourFor(status['user']['screen_name'])
        return ("%s%s% 16s%s %s " % (
            get_time_string(status, options),
            ansiFormatter.cmdColour(colour), status['user']['screen_name'],
            ansiFormatter.cmdReset(), align_text(replaceInStatus(status['text']))))

class VerboseStatusFormatter(object):
    def __call__(self, status, options):
        return ("-- %s (%s) on %s\n%s\n" % (
            status['user']['screen_name'],
            status['user']['location'],
            status['created_at'],
            gHtmlParser.unescape(status['text'])))

class JSONStatusFormatter(object):
    def __call__(self, status, options):
         status['text'] = gHtmlParser.unescape(status['text'])
         return json.dumps(status)

class URLStatusFormatter(object):
    urlmatch = re.compile(r'https?://\S+')
    def __call__(self, status, options):
        urls = self.urlmatch.findall(status['text'])
        return '\n'.join(urls) if urls else ""


class ListsFormatter(object):
    def __call__(self, list):
        if list['description']:
            list_str = "%-30s (%s)" % (list['name'], list['description'])
        else:
            list_str = "%-30s" % (list['name'])
        return "%s\n" % list_str

class ListsVerboseFormatter(object):
    def __call__(self, list):
        list_str = "%-30s\n description: %s\n members: %s\n mode:%s\n" % (list['name'], list['description'], list['member_count'], list['mode'])
        return list_str

class AnsiListsFormatter(object):
    def __init__(self):
        self._colourMap = ansi.ColourMap()

    def __call__(self, list):
        colour = self._colourMap.colourFor(list['name'])
        return ("%s%-15s%s %s" % (
            ansiFormatter.cmdColour(colour), list['name'],
            ansiFormatter.cmdReset(), list['description']))


class AdminFormatter(object):
    def __call__(self, action, user):
        user_str = "%s (%s)" % (user['screen_name'], user['name'])
        if action == "follow":
            return "You are now following %s.\n" % (user_str)
        else:
            return "You are no longer following %s.\n" % (user_str)

class VerboseAdminFormatter(object):
    def __call__(self, action, user):
        return("-- %s: %s (%s): %s" % (
            "Following" if action == "follow" else "Leaving",
            user['screen_name'],
            user['name'],
            user['url']))

class SearchFormatter(object):
    def __call__(self, result, options):
        return("%s%s %s" % (
            get_time_string(result, options, "%a, %d %b %Y %H:%M:%S +0000"),
            result['from_user'], result['text']))

class VerboseSearchFormatter(SearchFormatter):
    pass  # Default to the regular one

class URLSearchFormatter(object):
    urlmatch = re.compile(r'https?://\S+')
    def __call__(self, result, options):
        urls = self.urlmatch.findall(result['text'])
        return '\n'.join(urls) if urls else ""

class AnsiSearchFormatter(object):
    def __init__(self):
        self._colourMap = ansi.ColourMap()

    def __call__(self, result, options):
        colour = self._colourMap.colourFor(result['from_user'])
        return ("%s%s%s%s %s" % (
            get_time_string(result, options, "%a, %d %b %Y %H:%M:%S +0000"),
            ansiFormatter.cmdColour(colour), result['from_user'],
            ansiFormatter.cmdReset(), result['text']))

_term_encoding = None
def get_term_encoding():
    global _term_encoding
    if not _term_encoding:
        lang = os.getenv('LANG', 'unknown.UTF-8').split('.')
        if lang[1:]:
            _term_encoding = lang[1]
        else:
            _term_encoding = 'UTF-8'
    return _term_encoding

formatters = {}
status_formatters = {
    'default': StatusFormatter,
    'verbose': VerboseStatusFormatter,
    'json': JSONStatusFormatter,
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

lists_formatters = {
    'default': ListsFormatter,
    'verbose': ListsVerboseFormatter,
    'urls': None,
    'ansi': AnsiListsFormatter
}
formatters['lists'] = lists_formatters

def get_formatter(action_type, options):
    formatters_dict = formatters.get(action_type)
    if (not formatters_dict):
        raise TwitterError(
            "There was an error finding a class of formatters for your type (%s)"
            % (action_type))
    f = formatters_dict.get(options['format'])
    if (not f):
        raise TwitterError(
            "Unknown formatter '%s' for status actions" % (options['format']))
    return f()

class Action(object):

    def ask(self, subject='perform this action', careful=False):
        '''
        Requests from the user using `raw_input` if `subject` should be
        performed. When `careful`, the default answer is NO, otherwise YES.
        Returns the user answer in the form `True` or `False`.
        '''
        sample = '(y/N)'
        if not careful:
            sample = '(Y/n)'

        prompt = 'You really want to %s %s? ' % (subject, sample)
        try:
            answer = input(prompt).lower()
            if careful:
                return answer in ('yes', 'y')
            else:
                return answer not in ('no', 'n')
        except EOFError:
            print(file=sys.stderr)  # Put Newline since Enter was never pressed
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
                    sys.stdout.flush()
                    time.sleep(options['refresh_rate'])
            else:
                doAction()
        except KeyboardInterrupt:
            print('\n[Keyboard Interrupt]', file=sys.stderr)
            pass

class NoSuchActionError(Exception):
    pass

class NoSuchAction(Action):
    def __call__(self, twitter, options):
        raise NoSuchActionError("No such action: %s" % (options['action']))

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
        twitter.domain = "search.twitter.com"
        twitter.uriparts = ()
        # We need to bypass the TwitterCall parameter encoding, so we
        # don't encode the plus sign, so we have to encode it ourselves
        query_string = "+".join(
            [quote(term)
             for term in options['extra_args']])

        results = twitter.search(q=query_string)['results']
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
        except TwitterError as e:
            print("There was a problem following or leaving the specified user.")
            print("You may be trying to follow a user you are already following;")
            print("Leaving a user you are not currently following;")
            print("Or the user may not exist.")
            print("Sorry.")
            print()
            print(e)
        else:
            printNicely(af(options['action'], user))

class ListsAction(StatusAction):
    def getStatuses(self, twitter, options):
        if not options['extra_args']:
            raise TwitterError("Please provide a user to query for lists")

        screen_name = options['extra_args'][0]

        if not options['extra_args'][1:]:
            lists = twitter.lists.list(screen_name=screen_name)
            if not lists:
                printNicely("This user has no lists.")
            for list in lists:
                lf = get_formatter('lists', options)
                printNicely(lf(list))
            return []
        else:
            return reversed(twitter.lists.statuses(
                    owner_screen_name=screen_name, slug=options['extra_args'][1]))


class MyListsAction(ListsAction):
    def getStatuses(self, twitter, options):
        screen_name = twitter.account.verify_credentials()['screen_name']
        options['extra_args'].insert(0, screen_name)
        return ListsAction.getStatuses(self, twitter, options)


class FriendsAction(StatusAction):
    def getStatuses(self, twitter, options):
        return reversed(twitter.statuses.home_timeline(count=options["length"]))

class RepliesAction(StatusAction):
    def getStatuses(self, twitter, options):
        return reversed(twitter.statuses.mentions_timeline(count=options["length"]))

class FollowAction(AdminAction):
    def getUser(self, twitter, user):
        return twitter.friendships.create(screen_name=user)

class LeaveAction(AdminAction):
    def getUser(self, twitter, user):
        return twitter.friendships.destroy(screen_name=user)

class SetStatusAction(Action):
    def __call__(self, twitter, options):
        statusTxt = (" ".join(options['extra_args'])
                     if options['extra_args']
                     else str(input("message: ")))
        replies = []
        ptr = re.compile("@[\w_]+")
        while statusTxt:
            s = ptr.match(statusTxt)
            if s and s.start() == 0:
                replies.append(statusTxt[s.start():s.end()])
                statusTxt = statusTxt[s.end() + 1:]
            else:
                break
        replies = " ".join(replies)
        if len(replies) >= 140:
            # just go back
            statusTxt = replies
            replies = ""

        splitted = []
        while statusTxt:
            limit = 140 - len(replies)
            if len(statusTxt) > limit:
                end = string.rfind(statusTxt, ' ', 0, limit)
            else:
                end = limit
            splitted.append(" ".join((replies, statusTxt[:end])))
            statusTxt = statusTxt[end:]

        if options['invert_split']:
            splitted.reverse()
        for status in splitted:
            twitter.statuses.update(status=status)

class TwitterShell(Action):

    def render_prompt(self, prompt):
        '''Parses the `prompt` string and returns the rendered version'''
        prompt = prompt.strip("'").replace("\\'", "'")
        for colour in ansi.COLOURS_NAMED:
            if '[%s]' % (colour) in prompt:
                prompt = prompt.replace(
                    '[%s]' % (colour), ansiFormatter.cmdColourNamed(colour))
        prompt = prompt.replace('[R]', ansiFormatter.cmdReset())
        return prompt

    def __call__(self, twitter, options):
        prompt = self.render_prompt(options.get('prompt', 'twitter> '))
        while True:
            options['action'] = ""
            try:
                args = input(prompt).split()
                parse_args(args, options)
                if not options['action']:
                    continue
                elif options['action'] == 'exit':
                    raise SystemExit(0)
                elif options['action'] == 'shell':
                    print('Sorry Xzibit does not work here!', file=sys.stderr)
                    continue
                elif options['action'] == 'help':
                    print('''\ntwitter> `action`\n
                          The Shell Accepts all the command line actions along with:

                          exit    Leave the twitter shell (^D may also be used)

                          Full CMD Line help is appended below for your convinience.''', file=sys.stderr)
                Action()(twitter, options)
                options['action'] = ''
            except NoSuchActionError as e:
                print(e, file=sys.stderr)
            except KeyboardInterrupt:
                print('\n[Keyboard Interrupt]', file=sys.stderr)
            except EOFError:
                print(file=sys.stderr)
                leaving = self.ask(subject='Leave')
                if not leaving:
                    print('Excellent!', file=sys.stderr)
                else:
                    raise SystemExit(0)

class PythonPromptAction(Action):
    def __call__(self, twitter, options):
        try:
            while True:
                smrt_input(globals(), locals())
        except EOFError:
            pass

class HelpAction(Action):
    def __call__(self, twitter, options):
        print(__doc__)

class DoNothingAction(Action):
    def __call__(self, twitter, options):
        pass

class RateLimitStatus(Action):
    def __call__(self, twitter, options):
        rate = twitter.application.rate_limit_status()
        print("Remaining API requests: %s / %s (hourly limit)" % (rate['remaining_hits'], rate['hourly_limit']))
        print("Next reset in %ss (%s)" % (int(rate['reset_time_in_seconds'] - time.time()),
                                          time.asctime(time.localtime(rate['reset_time_in_seconds']))))

actions = {
    'authorize' : DoNothingAction,
    'follow'    : FollowAction,
    'friends'   : FriendsAction,
    'list'      : ListsAction,
    'mylist'    : MyListsAction,
    'help'      : HelpAction,
    'leave'     : LeaveAction,
    'pyprompt'  : PythonPromptAction,
    'replies'   : RepliesAction,
    'search'    : SearchAction,
    'set'       : SetStatusAction,
    'shell'     : TwitterShell,
    'rate'      : RateLimitStatus,
}

def loadConfig(filename):
    options = dict(OPTIONS)
    if os.path.exists(filename):
        cp = SafeConfigParser()
        cp.read([filename])
        for option in ('format', 'prompt'):
            if cp.has_option('twitter', option):
                options[option] = cp.get('twitter', option)
        # process booleans
        for option in ('invert_split',):
            if cp.has_option('twitter', option):
                options[option] = cp.getboolean('twitter', option)
    return options

def main(args=sys.argv[1:]):
    arg_options = {}
    try:
        parse_args(args, arg_options)
    except GetoptError as e:
        print("I can't do that, %s." % (e), file=sys.stderr)
        print(file=sys.stderr)
        raise SystemExit(1)

    config_path = os.path.expanduser(
        arg_options.get('config_filename') or OPTIONS.get('config_filename'))
    config_options = loadConfig(config_path)

    # Apply the various options in order, the most important applied last.
    # Defaults first, then what's read from config file, then command-line
    # arguments.
    options = dict(OPTIONS)
    for d in config_options, arg_options:
        for k, v in list(d.items()):
            if v: options[k] = v

    if options['refresh'] and options['action'] not in (
        'friends', 'replies'):
        print("You can only refresh the friends or replies actions.", file=sys.stderr)
        print("Use 'twitter -h' for help.", file=sys.stderr)
        return 1

    oauth_filename = os.path.expanduser(options['oauth_filename'])

    if (options['action'] == 'authorize'
        or not os.path.exists(oauth_filename)):
        oauth_dance(
            "the Command-Line Tool", CONSUMER_KEY, CONSUMER_SECRET,
            options['oauth_filename'])

    global ansiFormatter
    ansiFormatter = ansi.AnsiCmd(options["force-ansi"])

    oauth_token, oauth_token_secret = read_token_file(oauth_filename)

    twitter = Twitter(
        auth=OAuth(
            oauth_token, oauth_token_secret, CONSUMER_KEY, CONSUMER_SECRET),
        secure=options['secure'],
        api_version='1.1',
        domain='api.twitter.com')

    try:
        Action()(twitter, options)
    except NoSuchActionError as e:
        print(e, file=sys.stderr)
        raise SystemExit(1)
    except TwitterError as e:
        print(str(e), file=sys.stderr)
        print("Use 'twitter -h' for help.", file=sys.stderr)
        raise SystemExit(1)
