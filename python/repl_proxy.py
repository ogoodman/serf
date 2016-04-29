"""Proxy which does all operations on a given object in a specified thread.

The name is due to the fact that this is intended for use in Python's
Read-Eval-Print-Loop.
"""

import types
from serf.worker import Callback
from serf.serializer import POD_TYPES

def callWithResult(cb, func, *args):
    try:
        cb.success(func(*args))
    except Exception, e:
        cb.failure(e)

class REPLProxy(object):
    def __init__(self, target, tm):
        self.target = target
        self.tm = tm

    def _wrap(self, value):
        if type(value) in POD_TYPES:
            return value
        return REPLProxy(value, self.tm)

    def _getattr(self, name):
        attr = getattr(self.target, name)
        if type(attr) not in (types.FunctionType, types.MethodType):
            return self._wrap(attr)
        def _mcall(*args):
            cb = Callback()
            self.tm.callFromThread(callWithResult, cb, attr, *args)
            return self._wrap(cb.wait())
        return _mcall

    def __setattr__(self, name, value):
        if name in ('target', 'tm'):
            self.__dict__[name] = value
        else:
            setattr(self.target, name, value)

    def __getattr__(self, name):
        return self._getattr(name)

    def __getitem__(self, key):
        return self._getattr('__getitem__')(key)

    def __setitem__(self, key, value):
        self._getattr('__setitem__')(key, value)

    def __delitem__(self, key):
        self._getattr('__delitem__')(key)

    def __call__(self, *args):
        return self.__call__(*args)
