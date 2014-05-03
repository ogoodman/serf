"""Thread-safe handler for testing Transport.

See: net_test.py for usage example.
"""

import threading

class TestHandler(object):
    def __init__(self, transport=None):
        self.received = []
        self.cond = threading.Condition()
        self.expected = 0
        self.node_conn = None
        if transport is not None:
            transport.subscribe('connected', self.connected)
            transport.subscribe('message', self.handle)
            transport.subscribe('online', self.online)

    def handle(self, ev, msg):
        with self.cond:
            self.received.append(msg['message'])
            self.cond.notify()

    def online(self, ev, node):
        pass

    def connected(self, ev, node):
        self.node_conn = node

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        with self.cond:
            if self.expected == 0:
                self.cond.wait(.5)
                assert(len(self.received) == 0)
                return
            while len(self.received) < self.expected:
                prev = len(self.received)
                self.cond.wait(1)
                assert(len(self.received) != prev)
            # self.cond.wait(.2) # make sure no more come.
            assert(len(self.received) == self.expected)

    def expect(self, n):
        with self.cond:
            assert(len(self.received) == self.expected)
            self.received = []
            self.expected = n
            return self

