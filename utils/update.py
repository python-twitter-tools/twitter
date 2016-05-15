#!/usr/bin/env python

'''
DEPRECATED
This is a development script, intended for development use only.

This script generates the POST_ACTIONS variable
for placement in the twitter_globals.py

Example Usage:

    %prog >twitter/twitter_globals.py

Dependencies:

    (easy_install) BeautifulSoup
'''

import sys
from urllib import urlopen as _open
from BeautifulSoup import BeautifulSoup
from htmlentitydefs import codepoint2name

def uni2html(u):
    '''
    Convert unicode to html.

    Basically leaves ascii chars as is, and attempts to encode unicode chars
    as HTML entities. If the conversion fails the character is skipped.
    '''
    htmlentities = list()
    for c in u:
        ord_c = ord(c)
        if ord_c < 128:
            # ignoring all ^chars like ^M ^R ^E
            if ord_c >31:
                htmlentities.append(c)
        else:
            try:
                htmlentities.append('&%s;' % codepoint2name[ord_c])
            except KeyError:
                pass # Charachter unknown
    return ''.join(htmlentities)

def print_fw(iterable, joins=', ', prefix='', indent=0, width=79, trail=False):
    '''
    PPrint an iterable (of stringable elements).

        Entries are joined using `joins`
        A fixed_width (fw) is maintained of `width` chars per line
        Each line is indented with `indent`*4 spaces
        Lines are then prefixed with `prefix` string
        if `trail` a trailing comma is sent to stdout
        A newline is written after all is printed.
    '''
    shift_width = 4
    preline = '%s%s' %(' '*shift_width, prefix)
    linew = len(preline)
    sys.stdout.write(preline)
    for i, entry in enumerate(iterable):
        if not trail and i == len(iterable) - 1:
            sentry = str(entry)
        else:
            sentry = '%s%s' %(str(entry), joins)
        if linew + len(sentry) > width:
            sys.stdout.write('\n%s' %(preline))
            linew = len(preline)
        sys.stdout.write(sentry)
        linew += len(sentry)
    sys.stdout.write('\n')

def main_with_options(options, files):
    '''
    Main function the prints twitter's _POST_ACTIONS to stdout

    TODO: look at possibly dividing up this function
    '''

    apifile = _open('http://apiwiki.twitter.com/REST+API+Documentation')
    try:
        apihtml = uni2html(apifile.read())
    finally:
        apifile.close()

    ## Parsing the ApiWiki Page

    apidoc = BeautifulSoup(apihtml)
    toc = apidoc.find('div', {'class':'toc'})
    toc_entries = toc.findAll('li', text=lambda text: 'Methods' in text)
    method_links = {}
    for entry in toc_entries:
        links = entry.parent.parent.findAll('a')
        method_links[links[0].string] = [x['href'] for x in links[1:]]

    # Create unique hash of mehods with POST_ACTIONS
    POST_ACTION_HASH = {}
    for method_type, methods in method_links.items():
        for method in methods:
            # Strip the hash (#) mark from the method id/name
            method = method[1:]
            method_body = apidoc.find('a', {'name': method})
            value = list(method_body.findNext(
                    'b', text=lambda text: 'Method' in text
                ).parent.parent.childGenerator())[-1]
            if 'POST' in value:
                method_name = method_body.findNext('h3').string
                try:
                    POST_ACTION_HASH[method_name] += (method_type,)
                except KeyError:
                    POST_ACTION_HASH[method_name] = (method_type,)

    # Reverse the POST_ACTION_HASH
    # this is done to allow generation of nice comment strings
    POST_ACTION_HASH_R = {}
    for method, method_types in POST_ACTION_HASH.items():
        try:
            POST_ACTION_HASH_R[method_types].append(method)
        except KeyError:
            POST_ACTION_HASH_R[method_types] = [method]

    ## Print the POST_ACTIONS to stdout as a Python List
    print """'''
    This module is automatically generated using `update.py`

    .. data:: POST_ACTIONS
        List of twitter method names that require the use of POST
'''
"""
    print 'POST_ACTIONS = [\n'
    for method_types, methods in POST_ACTION_HASH_R.items():
        print_fw(method_types, prefix='# ', indent=1)
        print_fw([repr(str(x)) for x in methods], indent=1, trail=True)
        print ""
    print ']'

def main():
    import optparse

    class CustomFormatter(optparse.IndentedHelpFormatter):
        """formatter that overrides description reformatting."""
        def format_description(self, description):
            ''' indents each line in the description '''
            return "\n".join([
                "%s%s" %(" "*((self.level+1)*self.indent_increment), line)
                for line in description.splitlines()
            ]) + "\n"

    parser = optparse.OptionParser(
            formatter=CustomFormatter(),
            description=__doc__
        )
    (options, files) = parser.parse_args()
    main_with_options(options, files)


if __name__ == "__main__":
    main()
