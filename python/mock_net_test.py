#!/usr/bin/python

"""Tests for MockNet."""

import unittest
from serf.mock_net import MockNet

# It would be an encoded dictionary-like thing being passed in the
# real framework layer. If we don't feel the need to test serialization
# then we can pass dictionaries through the MockNet.

class MockHandler(object):
    def __init__(self, transport=None):
        self.received = []
        self.exc = None
        if transport is not None:
            transport.subscribe('message', self.handle)

    def handle(self, ev, msg):
        self.received.append(msg['message'])

    def failure(self, exc):
        self.exc = exc

class MockNetTest(unittest.TestCase):
    def test(self):
        net = MockNet()
        handler = MockHandler(net.addNode('A'))
        net.send('A', {'foo':'bar'})
        self.assertEqual(handler.received, [{'foo':'bar'}])

    def testSendFailure(self):
        net = MockNet()
        cb = MockHandler()
        net.send('A', {}) # no such node, no callback, fail silently.
        net.send('A', {}, errh=cb.failure)
        self.assertEqual(type(cb.exc), KeyError)

if __name__ == '__main__':
    unittest.main()
