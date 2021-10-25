"""
The minimalist yet fully featured Twitter API and Python toolset.

The Twitter and TwitterStream classes are the key to building your own
Twitter-enabled applications.

"""

from textwrap import dedent

from .api import Twitter, Twitter2, TwitterError, TwitterHTTPError, TwitterResponse
from .auth import NoAuth, UserPassAuth
from .oauth import (
    OAuth, read_token_file, write_token_file,
    __doc__ as oauth_doc)
from .oauth2 import (
    OAuth2, read_bearer_token_file, write_bearer_token_file,
    __doc__ as oauth2_doc)
from .stream import TwitterStream, TwitterStream2
from .oauth_dance import oauth_dance, oauth2_dance

__doc__ = __doc__ or ""

__doc__ += """
The Twitter class
-----------------
"""
__doc__ += dedent(Twitter.__doc__ or "")

__doc__ += """
The TwitterStream class
-----------------------
"""
__doc__ += dedent(TwitterStream.__doc__ or "")


__doc__ += """
Twitter Response Objects
------------------------
"""
__doc__ += dedent(TwitterResponse.__doc__ or "")


__doc__ += """
Authentication
--------------

You can authenticate with Twitter in three ways: NoAuth, OAuth, or
OAuth2 (app-only). Get help() on these classes to learn how to use them.

OAuth and OAuth2 are probably the most useful.


Working with OAuth
------------------
"""

__doc__ += dedent(oauth_doc or "")

__doc__ += """
Working with OAuth2
-------------------
"""

__doc__ += dedent(oauth2_doc or "")

__all__ = [
    "NoAuth",
    "OAuth",
    "OAuth2",
    "oauth2_dance",
    "oauth_dance",
    "read_bearer_token_file",
    "read_token_file",
    "Twitter",
    "Twitter2",
    "TwitterError",
    "TwitterHTTPError",
    "TwitterResponse",
    "TwitterStream",
    "TwitterStream2",
    "UserPassAuth",
    "write_bearer_token_file",
    "write_token_file",
    ]
