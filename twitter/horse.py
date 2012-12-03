"""
Horse-e

An automatic Twitter nonsense generator.


USAGE:

  horsee <--tweet or --print> wordsfile.txt

  Read text from wordsfile.txt and either print or tweet a generated
  nonsense phrase.

"""

from __future__ import print_function

from string import maketrans
import random
import sys
import os

from .api2 import TwitterAPI
from .oauth_dance import oauth_dance
from .oauth import read_token_file, OAuth


# lololol

t = maketrans( 
    "ABCDEFGHIJKLMabcdefghijklmNOPQRSTUVWXYZnopqrstuvwxyz", 
    "NOPQRSTUVWXYZnopqrstuvwxyzABCDEFGHIJKLMabcdefghijklm")
CONSUMER_KEY = "RE1Sw6xj8EGxkVGl85nxt".translate(t)
CONSUMER_SECRET = "z6bBg83tzag8Rollcz2iMLmzoWIo51oaVifi3DLzp".translate(t)

LEVELS = 2

def markhov_dict(words, levels=LEVELS):
    d = dict()
    for idx in xrange(len(words)):
        for level in xrange(1, levels+1):
            if idx - level < 0: continue
            key = tuple(([None] * (levels - level))
                        + [words[i] for i in xrange(idx-level-1, idx-1)])
            word = words[idx]
            wdict = d.get(key, {})
            wdict[word] = wdict.get(word, 0) + 1
            d[key] = wdict
    return d

def word_pairs(text):
    ws = [w.strip(",.!'()[]{}") for w in text.split()]
    words = [w0 + " " +  w1 for w0, w1 in zip(ws, ws[1:])]
    return words

def horsify(d, levels=LEVELS, min_words=1, max_words=12, max_length=140):
    first_word = random.choice(random.choice(d.values()).keys())
    words = [first_word]
    key = [None] * levels
    for _ in xrange(random.randint(min_words, max_words)):
        key = key[1:] + [words[-1]]
        for i in xrange(levels):
            k = ([None] * i) + key[i:]
            word_weights = d.get(tuple(k))
            if word_weights: break
        word_weights = word_weights.items()
        random.shuffle(word_weights)
        total = sum([v for k,v in word_weights])
        r = random.randint(0, total)
        for word, weight in word_weights:
            r -= weight
            if r <= 0: break
        words.append(word)
    l = 0
    out_words = []
    while words:
        word = words.pop(0)
        l += len(word)
        if l > max_length: break
        out_words.append(word)
    return ' '.join(out_words).capitalize()

def main():
    args = sys.argv[1:]
    if not args[1:] or args[0] not in ('--tweet', '--print'):
        print(__doc__)
        sys.exit(1)
    text = horsify(markhov_dict(word_pairs(open(args[1]).read().decode('utf-8'))))
    if args[0] == '--print':
        print(text)
    else:
        oauth_filename = os.environ.get('HOME', '') + os.sep + '.horsee_oauth'
        if not os.path.exists(oauth_filename):
            oauth_dance(
                "Horse-e", CONSUMER_KEY, CONSUMER_SECRET,
                oauth_filename)

        oauth_token, oauth_token_secret = read_token_file(oauth_filename)

        twitter = TwitterAPI(
            auth=OAuth(
                oauth_token, oauth_token_secret, CONSUMER_KEY, CONSUMER_SECRET))
        twitter.post('statuses/update', status=text)

