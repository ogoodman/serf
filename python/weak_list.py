"""A set which weakly references its members which may include methods."""

import weakref
import types

class WeakList(object):
    """A set which only weakly references its members.
    
    In addition to the the usual hashable types it can also
    hold instance methods which will be removed when the objects
    they were methods of become unreferenced.
    """
    def __init__(self):
        self._items = weakref.WeakKeyDictionary()

    def add(self, ob):
        """Add ob with a value of None."""
        self.set(ob, None)

    def set(self, ob, value):
        """Add ob to the set."""
        if type(ob) is types.MethodType:
            self._items[ob.im_self] = [ob.im_func.__name__, value]
            return hash(ob.im_self)
        else:
            self._items[ob] = [None, value]
            return hash(ob)

    def _find(self, ob_hash):
        for o in self._items:
            if hash(o) == ob_hash:
                return o

    def discard(self, ob):
        """Remove ob from the set if present."""
        if type(ob) in (int, long):
            found = self._find(ob)
            if found is not None:
                del self._items[found]
        elif type(ob) is types.MethodType:
            del self._items[ob.im_self]
        else:
            del self._items[ob]

    def keys(self):
        """Returns list of (strong refs to) the members."""
        return [k if v[0] is None else getattr(k, v[0]) for k, v in self._items.items()]

    def items(self):
        """Returns list of (key, value) pairs."""
        return [(k, v[1]) if v[0] is None else (getattr(k, v[0]), v[1]) for k, v in self._items.items()]

    def __len__(self):
        """Number of items in the set."""
        return len(self._items)

class SubAdapter(object):
    def __init__(self, subscriber, func, method_name):
        """Make a subscriber equivalent to lambda e, i: func(subscriber, e, i)."""
        self.subscriber = weakref.ref(subscriber)
        self.func = func
        self.method_name = method_name

    def __call__(self, event, info):
        """Calls func(subscriber, event, info) if subscriber is still live."""
        subscriber = self.subscriber()
        if subscriber is not None:
            if self.method_name is not None:
                subscriber = getattr(subscriber, self.method_name)
            self.func(subscriber, event, info)

def getAdapter(subscriber, func, name=None):
    """Makes a new subscriber equivalent to lambda e, i: func(subscriber, e, i).

    I.e. when the new subscriber is called, func gets to decide whether
    the original is called and, if so, what it is passed.

    The new subscriber is referenced by the original and only weakly references
    it so that (absent any other references to the new subscriber) it will
    become unreferenced as soon as the original is.
    """
    name = name or func.__name__ # key for this adapter
    if type(subscriber) is types.MethodType:
        method_name = subscriber.im_func.__name__
        subscriber = subscriber.im_self
    else:
        method_name = None
    arefs = getattr(subscriber, '_adapter_refs', None)
    if arefs is None:
        arefs = subscriber._adapter_refs = {}
    if name not in arefs:
        arefs[name] = SubAdapter(subscriber, func, method_name)
    return arefs[name]
