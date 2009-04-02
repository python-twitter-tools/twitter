"""
Support for ANSI colours in command-line client.

.. data:: ESC
    ansi escape character

.. data:: RESET
    ansi reset colour (ansi value)

.. data:: COLOURS_NAMED
    dict of colour names mapped to their ansi value

.. data:: COLOURS_MIDS
    A list of ansi values for Mid Spectrum Colours
"""

import itertools
import sys

ESC = chr(0x1B)
RESET = "0"

COLOURS_NAMED = dict(zip(
    ['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'],
    [str(x) for x in range(30, 38)]
))
COLOURS_MIDS = [
    colour for name, colour in COLOURS_NAMED.items()
    if name not in ('black', 'white')
]

class AnsiColourException(Exception):
    ''' Exception while processing ansi colours '''
    pass

class ColourMap(object):
    '''
    Object that allows for mapping strings to ansi colour values.
    '''
    def __init__(self, colors=COLOURS_MIDS):
        ''' uses the list of ansi `colors` values to initialize the map '''
        self._cmap = {}
        self._colourIter = itertools.cycle(colors)

    def colourFor(self, string):
        '''
        Returns an ansi colour value given a `string`.
        The same ansi colour value is always returned for the same string
        '''
        if not self._cmap.has_key(string):
            self._cmap[string] = self._colourIter.next()
        return self._cmap[string]

def cmdReset():
    ''' Returns the ansi cmd colour for a RESET '''
    if sys.stdout.isatty():
        return ESC + "[0m"
    else:
        return ""

def cmdColour(colour):
    '''
    Return the ansi cmd colour (i.e. escape sequence)
    for the ansi `colour` value
    '''
    if sys.stdout.isatty():
        return ESC + "[" + colour + "m"
    else:
        return ""

def cmdColourNamed(colour):
    ''' Return the ansi cmdColour for a given named `colour` '''
    try:
        return cmdColour(COLOURS_NAMED[colour])
    except KeyError:
        raise AnsiColourException('Unknown Colour %s' %(colour))
