import sys, traceback
import random
import types
from serf.weak_list import WeakList
from serf.bound_method import BoundMethod
from serf.ref import RefError

class KeyList(object):
    """Set of persistent objects tracked by equality test or numeric key."""

    serialize = ('objs',)

    def __init__(self, objs=None):
        self.objs = objs or {}

    def add(self, cb):
        """Adds cb if no object comparing equal to it is present.

        Returns a random integer key if cb was added, else None.
        """
        return self.set(cb, None)

    def set(self, cb, value):
        for k, v in self.objs.items():
            if cb == v[0]:
                self.objs[k] = (cb, value)
                return k
        k = random.getrandbits(32)
        self.objs[k] = (cb, value)
        return k

    def discard(self, cb):
        """Removes any object comparing equal to cb.

        Or, if cb is a number, removes an object by key.
        """
        if type(cb) in (int, long):
            self.objs.pop(cb, None)
        else:
            for k, v in self.objs.items():
                if v[0] == cb:
                    del self.objs[k]
                    break

    def items(self):
        """Returns a list of the contained objects."""
        return self.objs.values()


class Publisher(object):
    serialize = ('_subs',)

    def __init__(self, subs=None):
        self._s = {}
        self._subs = subs or {}

    def notify(self, event, info):
        """Calls all event subscribers with args (event, info).

        If any subscriber throws an exception or returns False
        it will be unsubscribed from future notifications.
        """
        for sub, args in self.subscribers(event):
            try:
                if sub(event, info, *args) is False:
                    self.unsubscribe(event, sub)
            except RefError, e:
                self.unsubscribe(event, sub, True)
            except Exception, e:
                traceback.print_exc()
                print >>sys.stderr, 'delivering event:', event

    def subscribe(self, event, cb, args=(), persist=False):
        """Adds cb as a subscriber to the named event.

        If persist is True, cb must be a persistent object or
        method thereof.

        Any args will be added to the call when cb is called:
        cb(event, info, *args).
        """
        if persist:
            if type(cb) is types.MethodType:
                cb = BoundMethod(cb.im_self, cb.im_func.__name__)
            if event not in self._subs:
                self._subs[event] = KeyList()
            subid = self._subs[event].set(cb, args)
            self._save()
            return subid
        else:
            if event not in self._s:
                self._s[event] = WeakList()
            return self._s[event].set(cb, args)

    def unsubscribe(self, event, cb, persist=False):
        """Removes cb as a subscriber to the named event."""
        try:
            if persist:
                if type(cb) is types.MethodType:
                    cb = BoundMethod(cb.im_self, ob.im_func.__name__)
                self._subs[event].discard(cb)
                self._save()
            else:
                self._s[event].discard(cb)
        except KeyError:
            pass

    def subscribers(self, event):
        """Returns a list of subscribers to the named event."""
        return self._s.get(event, {}).items() + self._subs.get(event, {}).items()

    def _save(self):
        """Save only if we are persistent."""
        if hasattr(self, 'ref'):
            self.ref._save()
