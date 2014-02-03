"""
The minimalist yet fully featured Twitter API and Python toolset.

The Twitter and TwitterStream classes are the key to building your own
Twitter-enabled applications.

"""

from textwrap import dedent

from .api import Twitter, TwitterError, TwitterHTTPError, TwitterResponse
from .auth import NoAuth, UserPassAuth
from .oauth import (OAuth, read_token_file, write_token_file,
                    __doc__ as oauth_doc)
from .oauth2 import OAuth2
from .stream import TwitterStream
from .oauth_dance import oauth_dance

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
UserPassAuth. Get help() on these classes to learn how to use them.

OAuth is probably the most useful.


Working with OAuth
------------------
"""

__doc__ += dedent(oauth_doc or "")

__all__ = ["Twitter", "TwitterStream", "TwitterResponse", "TwitterError",
           "TwitterHTTPError", "NoAuth", "OAuth", "UserPassAuth",
           "read_token_file", "write_token_file", "oauth_dance", "OAuth2"]
