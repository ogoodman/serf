"""Utility functions."""

import getopt
import inspect
import os
import sys
import time
from random import choice
import string

def randomString(length=12):
    chars = string.uppercase + string.digits
    return ''.join([choice(chars) for i in xrange(length)])

class EqualityMixin(object):
    def __eq__(self, other):
        return (type(self) == type(other) and
                self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self.__eq__(other)

def rmapDict(func, d):
    return dict([(k, rmap(func, v)) for k, v in d.iteritems()])

def rmapList(func, l):
    return [rmap(func, x) for x in l]

def rmapTuple(func, t):
    return tuple(rmapList(func, t))

RMAP = {
    list: rmapList,
    dict: rmapDict,
    tuple: rmapTuple
}

def rmap(func, info):
    try:
        mapfn = RMAP[type(info)]
    except KeyError:
        return func(info)
    return mapfn(func, info)

def getOptions(short, long=None, help=None):
    """Functional wrapper for getopt.

    Instead of returning options as (opt, arg) pairs it returns a
    function which can be called to query each option. If supplied a
    help function will be called if invalid options are provided or if
    any of -h or --help are found.

    Args:
        short: single-letter options as string (see getopt).
        long: array of long options (see getopt).
        help: function to call before exit if command line is invalid.
    Returns:
        opt: function returning an option's value, True or None.
        args: non-option arguments as array of strings.
    """
    def printHelp():
        if isinstance(help, basestring):
            print help
        elif help is None:
            print inspect.stack()[2][0].f_globals['__doc__']
        else:
            help()
        sys.exit()

    try:
        opts, args = getopt.getopt(sys.argv[1:], short, long or [])
    except getopt.GetoptError, e:
        printHelp()

    opt_dict = {}
    for o, a in opts:
        if not o in opt_dict:
            opt_dict[o] = [a]
        else:
            opt_dict[o].append(a)

    if '-h' in opt_dict or '--help' in opt_dict:
        printHelp()

    def opt(options, default=None, all=False):
        """Get the value of an option or flag.

        Args:
            options: comma separated list of options to query.
            default: value to return if option was not supplied.
            all: return list of all values supplied with these options.
        Returns:
            Value of option, if supplied or True if option takes no arguments,
            otherwise None, or default if supplied.
        """
        values = []
        for option in options.split(','):
            if option in opt_dict:
                values.extend(opt_dict[option])
        if all:
            return values
        if not values:
            return default
        return values[-1] or True

    return opt, args

def timeCall(fn, *args):
    begin = time.time()
    fn(*args)
    print time.time() - begin

def importSymbol(path):
    mod_name, sym_name = path.rsplit('.', 1)
    mod = __import__(mod_name, fromlist=['*'])
    return getattr(mod, sym_name)

def codeDir():
    return os.path.dirname(__file__)
