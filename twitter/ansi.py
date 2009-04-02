"""
Support for ANSI colours in command-line client.

"""

import itertools
import sys

ESC = chr(0x1B)
RESET = "0"

COLOURS = [str(x) for x in range(31, 37)]

class ColourMap(object):
    def __init__(self):
        self._cmap = {}
        self._colourIter = itertools.cycle(COLOURS)
        
    def colourFor(self, string):
        if not self._cmap.has_key(string):
            self._cmap[string] = self._colourIter.next()
        return self._cmap[string]

def cmdReset():
    if sys.stdout.isatty():
        return ESC + "[0m"
    else:
        return ""

def cmdColour(colour):
    if sys.stdout.isatty():
        return ESC + "[" + colour + "m"
    else:
        return ""
