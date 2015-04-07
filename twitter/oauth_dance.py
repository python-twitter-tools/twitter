from __future__ import print_function

import webbrowser
import time

from .api import Twitter, json
from .oauth import OAuth, write_token_file
from .oauth2 import OAuth2, write_bearer_token_file

try:
    _input = raw_input
except NameError:
    _input = input


def oauth2_dance(consumer_key, consumer_secret, token_filename=None):
    """
    Perform the OAuth2 dance to transform a consumer key and secret into a
    bearer token.

    If a token_filename is given, the bearer token will be written to
    the file.
    """
    twitter = Twitter(
        auth=OAuth2(consumer_key=consumer_key, consumer_secret=consumer_secret),
        format="",
        api_version="")
    token = json.loads(twitter.oauth2.token(grant_type="client_credentials"))["access_token"]
    if token_filename:
        write_bearer_token_file(token)
    return token

def oauth_dance(app_name, consumer_key, consumer_secret, token_filename=None):
    """
    Perform the OAuth dance with some command-line prompts. Return the
    oauth_token and oauth_token_secret.

    Provide the name of your app in `app_name`, your consumer_key, and
    consumer_secret. This function will open a web browser to let the
    user allow your app to access their Twitter account. PIN
    authentication is used.

    If a token_filename is given, the oauth tokens will be written to
    the file.
    """
    print("Hi there! We're gonna get you all set up to use %s." % app_name)
    twitter = Twitter(
        auth=OAuth('', '', consumer_key, consumer_secret),
        format='', api_version=None)
    oauth_token, oauth_token_secret = parse_oauth_tokens(
        twitter.oauth.request_token(oauth_callback="oob"))
    print("""
In the web browser window that opens please choose to Allow
access. Copy the PIN number that appears on the next page and paste or
type it here:
""")
    oauth_url = ('https://api.twitter.com/oauth/authorize?oauth_token=' +
                 oauth_token)
    print("Opening: %s\n" % oauth_url)

    try:
        r = webbrowser.open(oauth_url)
        time.sleep(2) # Sometimes the last command can print some
                      # crap. Wait a bit so it doesn't mess up the next
                      # prompt.
        if not r:
            raise Exception()
    except:
        print("""
Uh, I couldn't open a browser on your computer. Please go here to get
your PIN:

""" + oauth_url)
    oauth_verifier = _input("Please enter the PIN: ").strip()
    twitter = Twitter(
        auth=OAuth(
            oauth_token, oauth_token_secret, consumer_key, consumer_secret),
        format='', api_version=None)
    oauth_token, oauth_token_secret = parse_oauth_tokens(
        twitter.oauth.access_token(oauth_verifier=oauth_verifier))
    if token_filename:
        write_token_file(
            token_filename, oauth_token, oauth_token_secret)
        print()
        print("That's it! Your authorization keys have been written to %s." % (
            token_filename))
    return oauth_token, oauth_token_secret

def parse_oauth_tokens(result):
    for r in result.split('&'):
        k, v = r.split('=')
        if k == 'oauth_token':
            oauth_token = v
        elif k == 'oauth_token_secret':
            oauth_token_secret = v
    return oauth_token, oauth_token_secret
