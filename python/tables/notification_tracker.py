"""Helper class for testing Publishers of asynchronous events."""

import threading

class NotificationTracker(object):
    """A context manager (Python's term) to count notifications in a scope.

    Usage:

      tracker = NotificationTracker

      db.subscribe('change', tracker.callback)
      with tracker.expect(1):
          db.set(9, 'hi')
    
    This will raise an assertion unless exactly one call is made to the
    tracker's callback by the code in the scope. It has a 1 second
    timeout to cater for the fact that notifications are asynchronous.

    You can also do:

       with tracker.expect(0):
           db.doSomething(..)

    and if a notification arrives within half a second of getting to
    the bottom of the scope an assertion will be raised.
    """
    def __init__(self, fast=False):
        self.expected = 0
        self.count = 0
        self.events = []
        self.cond = threading.Condition()
        self.fast = fast

    def expect(self, n):
        with self.cond:
            assert(self.count == self.expected)
            self.expected = n
            self.count = 0
            self.events = []
            return self

    def callback(self, event, info):
        with self.cond:
            self.count += 1
            self.cond.notify()
            self.events.append(info)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        with self.cond:
            if self.expected == 0:
                if not self.fast:
                    self.cond.wait(.5)
                assert(self.count == 0)
                return
            while self.count < self.expected:
                prev = self.count
                self.cond.wait(1)
                assert(self.count != prev)
            if not self.fast:
                self.cond.wait(.2) # make sure no more come.
            assert(self.count == self.expected)

    def finish(self):
        # Only needed if running fast: then we should wait at the
        # end for any stragglers.
        with self.cond:
            self.cond.wait(.2)
            assert(self.count == self.expected)
