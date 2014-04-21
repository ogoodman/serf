#!/usr/bin/python

"""Tests for rpc_handler module."""

import unittest
import weakref
from rpc_handler import RPCHandler
from publisher import Publisher
from model import Model

class MockTransport(Publisher):
    client_ip = 'ip'
    def send(self, node, message, errh=None):
        self.peer.notify('message', message)

class RPCHandlerTest(unittest.TestCase):
    def testGC(self):
        h = RPCHandler(Publisher())
        h.makeBoundMethod({'o':'shared', 'm':'notify'})
        hr = weakref.ref(h)
        self.assertEqual(hr(), h)
        del h
        self.assertEqual(hr(), None)

    def testRPC(self):
        ta = MockTransport()
        tb = MockTransport()
        ta.peer = tb
        tb.peer = ta

        na = RPCHandler(ta)
        nb = RPCHandler(tb)

        oa = Model()
        na.provide(1, oa)

        rset = nb.makeBoundMethod({'o':1, 'm':'set'})
        rset('x', 1)

        self.assertEqual(oa.get('x'), 1)

if __name__ == '__main__':
    unittest.main()
