"""Test handler for transport.Transport.

Regular condition variables don't work because a greenlet blocked on a normal
condition variable cannot yield.

See: net_test.py for usage example.

NOTE: test_handler.py also works if we import threading from eventlet.green
instead of the usual one.
"""

from eventlet.event import Event
from eventlet.timeout import Timeout

class TestHandler(object):
    def __init__(self, transport=None):
        self.received = []
        self.event = None
        self.expected = 0
        self.node_conn = None
        if transport is not None:
            transport.subscribe('connected', self.connected)
            transport.subscribe('message', self.handle)
            transport.subscribe('online', self.online)

    def handle(self, ev, msg):
        self.received.append(msg['message'])
        if len(self.received) == self.expected:
            self.event.send()

    def msg(self, msg):
        self.handle('message', {'message': msg})

    def online(self, ev, node):
        pass

    def connected(self, ev, node):
        self.node_conn = node

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if self.expected == 0:
            with Timeout(.5, None):
                self.event.wait()
            assert(len(self.received) == 0)
            return
        with Timeout(1):
            self.event.wait()
            self.event = Event()
        # could wait a bit longer to ensure no extras are received.

    def expect(self, n):
        assert(len(self.received) == self.expected)
        self.received = []
        self.expected = n
        self.event = Event()
        return self
