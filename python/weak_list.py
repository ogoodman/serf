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
        """Add ob to the set."""
        if type(ob) is types.MethodType:
            self._items[ob.im_self] = ob.im_func.__name__
        else:
            self._items[ob] = None
    def discard(self, ob):
        """Remove ob from the set if present."""
        if type(ob) is types.MethodType:
            del self._items[ob.im_self]
        else:
            del self._items[ob]
    def items(self):
        """Returns list of (strong refs to) the members."""
        return [k if v is None else getattr(k, v) for k, v in self._items.items()]
    def __len__(self):
        """Number of items in the set."""
        return len(self._items)
