#!/usr/bin/python

"""Tests for reliable replication."""

import unittest
from serf.mock_net import MockNet
from serf.test_fs import TestFS
from serf.proxy import Proxy

from serf.po.file import File
from serf.po.call_log import CallLog
from serf.po.printer import Printer
from serf.po.node_observer import NodeObserver

class CallLogTest(unittest.TestCase):
    def test(self):
        net = MockNet()
        va, ra = net.addRPCHandler('A', '', TestFS())
        vb, rb = net.addRPCHandler('B', '', TestFS())

        ea, eb = va.resources['#env'], vb.resources['#env']

        cl = va.makeRef(CallLog(ea))

        # We'll use a call log as the replication target.
        clb = vb.makeRef(CallLog(eb))

        p = ra.makeProxy(clb._path, 'B')

        cl.say('hi')
        cl.say('bye')

        r = cl.addReader('1', p, 0)

        self.assertEqual(cl.end(), 2)
        self.assertEqual(cl[0], ['say', ['hi']])
        self.assertEqual(clb.end(), 0)

        r.start()

        self.assertEqual(clb.end(), 2)
        self.assertEqual(clb[0], ['say', ['hi']])

        cl.say('foo')

        self.assertEqual(clb.end(), 3)
        self.assertEqual(clb[2], ['say', ['foo']])

        net.goOffline('B')

        cl.say('bar')

        self.assertEqual(cl.end(), 4)
        self.assertEqual(clb.end(), 3)

        net.goOnline('B')

        self.assertEqual(clb.end(), 4)
        self.assertEqual(clb[3], ['say', ['bar']])

        # Check everything is persistent.
        va.clearCache()
        vb.clearCache()

        cl.say('baz')

        self.assertEqual(clb.end(), 5)
        self.assertEqual(clb[4], ['say', ['baz']])

        r = cl.getReader('1')
        r.stop()

        cl.say('garply')

        self.assertEqual(clb.end(), 5)

        net.goOffline('B')
        r.start()

        self.assertEqual(clb.end(), 5)

        net.goOnline('B')

        self.assertEqual(clb.end(), 6)
        self.assertEqual(clb[5], ['say', ['garply']])

        cl.removeReader('1')

        cl.say('xyzzy')

        self.assertEqual(clb.end(), 6)
        self.assertEqual(cl.end(), 7)

        r = cl.addReader('2', p, 6)
        r.start()

        self.assertEqual(clb.end(), 7)

if __name__ == '__main__':
    unittest.main()
