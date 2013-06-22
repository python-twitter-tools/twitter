"""
The minimalist yet fully featured Twitter API and Python toolset.

api2 is the best, and most supported way to build your own Twitter
applications with Python.

"""

from textwrap import dedent

from .api import Twitter, TwitterError, TwitterHTTPError, TwitterResponse
from .auth import NoAuth, UserPassAuth
from .oauth import (OAuth, read_token_file, write_token_file,
                    __doc__ as oauth_doc)
from .oauth2 import OAuth2
from .stream import TwitterStream
from .oauth_dance import oauth_dance

from . import api2

from .api2 import TwitterAPIError


# Who needs Sphinx? Not me!

__doc__ += dedent(api2.__doc__)


__doc__ += """
**The legacy API below is deprecated and should not be used.**
==============================================================

The Twitter class
-----------------
"""
__doc__ += dedent(Twitter.__doc__)

__doc__ += """
The TwitterStream class
-----------------------
"""
__doc__ += dedent(TwitterStream.__doc__)


__doc__ += """
Twitter Response Objects
------------------------
"""
__doc__ += dedent(TwitterResponse.__doc__)


__doc__ += """
Authentication
--------------

You can authenticate with Twitter in three ways: NoAuth, OAuth, or
UserPassAuth. Get help() on these classes to learn how to use them.

OAuth is probably the most useful.


Working with OAuth
------------------
"""

__doc__ += dedent(oauth_doc)

__all__ = ["Twitter", "TwitterStream", "TwitterResponse", "TwitterError",
           "TwitterHTTPError", "NoAuth", "OAuth", "UserPassAuth",
           "read_token_file", "write_token_file", "oauth_dance", "OAuth2"]
