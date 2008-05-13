"""
Internal utility functions.

`htmlentitydecode` came from here:
    http://wiki.python.org/moin/EscapingHtml
"""


import re
from htmlentitydefs import name2codepoint

def htmlentitydecode(s):
    return re.sub(
        '&(%s);' % '|'.join(name2codepoint), 
        lambda m: unichr(name2codepoint[m.group(1)]), s)

__all__ = ["htmlentitydecode"]
