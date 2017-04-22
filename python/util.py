"""Utility functions."""

import getopt
import inspect
import os
import sys
import time
from cStringIO import StringIO
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
        opts, args = [], []

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

def dataRoot():
    """For demos, returns what should be a writable directory."""
    who = os.popen('whoami').read().strip()
    if who == 'root':
        data_root = '/var/lib/serf'
    else:
        home = os.getenv('HOME')
        if not home:
            raise Exception('dataRoot: $HOME is not set')
        data_root = os.path.join(home, '.serf-data')
    if not os.path.exists(data_root):
        os.makedirs(data_root)
    return data_root

class IndentingStream(object):
    """Wrapper for a file-like object which handles indentation."""
    def __init__(self, out):
        self.level = 0
        self.out = out
        self.done_indent = False

    def writeln(self, line):
        """Write line to self.out indented by the current level."""
        if not self.done_indent:
            self.out.write('    ' * self.level)
        self.out.write(line)
        self.out.write('\n')
        self.done_indent = False

    def write(self, s):
        """Write s to self.out indenting each line by the current level."""
        lines = s.split('\n')
        for line in lines[:-1]:
            self.writeln(line)
        if lines[-1]:
            if not self.done_indent:
                self.out.write('    ' * self.level)
            self.out.write(lines[-1])
            self.done_indent = True

    def indent(self, n):
        """Add n to the current indent level."""
        self.level += n

class Capture(object):
    def __init__(self, stream='stdout'):
        self.stream = stream
        self.old = getattr(sys, stream)
        self.fh = StringIO()
        setattr(sys, stream, self.fh)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        setattr(sys, self.stream, self.old)

    def getvalue(self):
        return self.fh.getvalue()
