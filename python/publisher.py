import sys, traceback
import random
import types
import weakref
from serf.storage import save_fn
from serf.util import removeAll
from serf.ref import RefError

WEAK, NORMAL, PERSISTENT = 0, 1, 2

class EventBinder(object):
    """EventBinder makes a subscriber from an instance method or callable.

    An instance method must be supplied as the receiver (self object) and
    method name. A callable should be supplied as the receiver with a
    method of None. We don't support bound methods directly because they
    can't be serialized, whereas a Ref or Proxy plus method name can.

    Calls to `.notify(event, info)` will result in a call of
    the method or callable, passing `(event, info, *args)`.

    Equality testing is done via the `id` which defaults to a random
    integer for PERSISTENT subscribers or `hash(receiver)` otherwise.
    """
    serialize = ('event', 'receiver', 'method', 'args', 'id')

    def __init__(self, event, receiver, method, args=(), id=None, how=None):
        self.event = event
        if how == WEAK and receiver is not None:
            self.receiver = weakref.ref(receiver)
        else:
            self.receiver = receiver
        self.method = method
        self.args = args
        self.id = id or (random.getrandbits(32) if how==PERSISTENT else hash(receiver))
        self.how = PERSISTENT if how is None else how

    def wants(self, event):
        return self.event == event or self.event == '*'

    def notify(self, event, info):
        receiver = self.receiver() if self.how==WEAK else self.receiver
        if receiver is None:
            return False
        try:
            cb = receiver if self.method is None else getattr(receiver, self.method)
            return cb(event, info, *self.args)
        except RefError:
            return False

    def handle(self):
        if self.how==WEAK:
            return self.receiver()
        return None

    def __eq__(self, other):
        if type(other) is not type(self):
            return False
        return self.event == other.event and self.id == other.id

class SubscribeMixin(object):
    """Adds subscribe and unsubscribe methods to classes that implement
    addSub and removeSub.
    """

    def subscribe(self, event, cb, args=(), how=WEAK):
        """Adds callable cb as a subscriber to the named event.

        When the publisher notifies of an event, via `notify(event, info)`,
        `cb` will be called as:

            cb(event, info, *args)

        If the call returns `False` or a `serf.ref.RefError` the subscription
        will be automatically removed.

        If how=WEAK, cb or the receiver if cb is a bound method,
        will be held weakly by the publisher. If how=PERSISTENT cb
        must be serializable or a bound method of such.

        A subscriber id is returned which may be used to unsubscribe.
        """
        if type(cb) is types.MethodType:
            sub = EventBinder(event, cb.im_self, cb.im_func.__name__, args, None, how)
        else:
            sub = EventBinder(event, cb, None, args, None, how)
        self.addSub(sub)
        return sub.id

    def unsubscribe(self, event, cb, how=WEAK):
        """Removes cb as a subscriber to the named event.

        For non-persistent subscriptions, the original `cb` may be
        passed or the subscriber-id returned from the subscribe call.

        For persistent subscriptions, the subscriber-id must always
        be used.
        """
        if type(cb) in (int, long):
            sub = EventBinder(event, None, None, (), cb, how)
        elif type(cb) is types.MethodType:
            sub = EventBinder(event, cb.im_self, cb.im_func.__name__, (), None, how)
        else:
            sub = EventBinder(event, cb, None, (), None, how)
        self.removeSub(sub)

class Publisher(SubscribeMixin):
    serialize = ('_subs',)

    def __init__(self, subs=None):
        self._w = weakref.WeakKeyDictionary()
        self._s = []
        self._subs = subs or []
        if type(subs) is dict:
            self._subs = convertSubs(subs)

    def addSub(self, sub):
        """Adds a subscriber.

        A subscriber `sub` must implement the following methods
        and properties:

            sub.how                 # -> WEAK, NORMAL or PERSISTENT
            sub.wants(event)        # -> True if event is of interest
            sub.notify(event, info) # deliver the event
            sub.__eq__(other)       # implements ==

        In addition:

            * if sub.how == PERSISTENT it must be serializable

            * if sub.how == WEAK, sub.handle() must return an object
              that can be made into a weak reference.

        If two subscribers which compare as equal are added, only
        the first will be kept. Equality testing is also used
        when removing subscribers.
        """
        if sub.how == PERSISTENT:
            if sub not in self._subs:
                self._subs.append(sub)
            self._save()
        elif sub.how == NORMAL:
            if sub not in self._s:
                self._s.append(sub)
        else:
            h = sub.handle()
            if h is None:
                return
            if h not in self._w:
                self._w[h] = [sub]
            else:
                subs = self._w[h]
                if sub not in subs:
                    subs.append(sub)

    def removeSub(self, sub):
        """Removes a subscriber.

        Only sub.how and equality testing are required of the
        object passed to removeSub. All subscribers comparing equal
        to `sub` will be removed.
        """
        if sub.how == PERSISTENT:
            removeAll(self._subs, sub)
            self._save()
        elif sub.how == NORMAL:
            removeAll(self._s, sub)
        else:
            for k in list(self._w):
                subs = self._w[k]
                removeAll(subs, sub)
                if not subs:
                    del self._w[k]

    def notify(self, event, info):
        """Notifies all event subscribers with args (event, info).

        If any subscriber returns False it will be removed.

        If info is callable, it will be called to get the info
        for the event, but only if the event has subscribers.
        This allows us to avoid expensive info computation when
        there are no subscribers.
        """
        subs = self.subscribers(event)
        if subs and callable(info):
            info = info()
        for sub in subs:
            try:
                if sub.notify(event, info) is False:
                    self.removeSub(sub)
            except Exception, e:
                traceback.print_exc()
                print >>sys.stderr, 'delivering event:', event

    def subscribers(self, event):
        """Returns a list of subscribers to the named event."""
        subs = [s for s in self._subs + self._s if s.wants(event)]
        for sl in self._w.values():
            for s in sl:
                if s.wants(event):
                    subs.append(s)
        return subs

    _save = save_fn


# Conversion helper.

class KeyList(object):
    """Set of persistent objects tracked by equality test or numeric key."""

    serialize = ('objs',)

    def __init__(self, objs=None):
        self.objs = objs or {}

def convertSubs(subs):
    new_subs = []
    for event, keylist in subs.items():
        for id, cba in keylist.objs.items():
            bm, args = cba
            print 'convertSubs', event, bm.target, bm.method, args, id
            new_subs.append(EventBinder(event, bm.target, bm.method, args, id))
    return new_subs
