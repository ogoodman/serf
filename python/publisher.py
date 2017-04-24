import sys, traceback
from weak_list import WeakList

class Publisher(object):
    def __init__(self):
        self._subs = {}

    def notify(self, event, info):
        """Calls all event subscribers with args (event, info).

        If any subscriber throws an exception or returns False
        it will be unsubscribed from future notifications.
        """
        for sub in self.subscribers(event):
            try:
                if sub(event, info) is False:
                    self.unsubscribe(event, sub)
            except Exception, e:
                traceback.print_exc()
                print >>sys.stderr, 'delivering event:', event

    def subscribe(self, event, cb):
        """Adds cb as a subscriber to the named event."""
        if event not in self._subs:
            self._subs[event] = WeakList()
        return self._subs[event].add(cb)

    def unsubscribe(self, event, cb):
        """Removes cb as a subscriber to the named event."""
        try:
            self._subs[event].discard(cb)
        except KeyError:
            pass

    def subscribers(self, event):
        """Returns a list of subscribers to the named event."""
        return self._subs.get(event, {}).items()
