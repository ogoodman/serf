"""Prints calls made on it."""

from fred.util import EqualityMixin

class Printer(EqualityMixin):
    serialize = ()

    def __getattr__(self, name):
        def pcall(*args):
            print '%s(%s)' % (name, ', '.join([repr(a) for a in args]))
        return pcall
