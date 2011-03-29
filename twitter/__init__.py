"""
The minimalist yet fully featured Twitter API and Python toolset.

The Twitter and TwitterStream classes are the key to building your own
Twitter-enabled applications.

"""

from .api import Twitter, TwitterError, TwitterHTTPError, TwitterResponse
from .auth import NoAuth, UserPassAuth
from .oauth import OAuth, read_token_file, write_token_file
from .stream import TwitterStream


# Who needs Sphinx? Not me!

__doc__ += """
The Twitter class
=================
"""
__doc__ += Twitter.__doc__

__doc__ += """
The TwitterStream class
=======================
"""
__doc__ += TwitterStream.__doc__


__doc__ += """
Twitter Response Objects
========================
"""
__doc__ += TwitterResponse.__doc__


__doc__ += """
Authentication Objects
======================

You can authenticate with Twitter in three ways: NoAuth, OAuth, or
UserPassAuth. Get help() on these classes to learn how to use them.


Other things
============

read_token_file and write_token_file are utility methods to read and
write OAuth token and secret key values. The values are stored as
strings in the file. Not terribly exciting.
"""

__all__ = ["Twitter", "TwitterStream", "TwitterResponse", "TwitterError",
           "TwitterHTTPError", "NoAuth", "OAuth", "UserPassAuth",
           "read_token_file", "write_token_file"]
