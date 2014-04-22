#!/usr/bin/python

"""Tests for the dispatcher module."""

import unittest
from serf.dispatcher import Dispatcher
from serf.publisher import Publisher
from serf.serialize import encodes
from serf.mock_net import MockEndpoint

class Listener(object):
    def __init__(self, endpoint):
        self.received = []
        endpoint.subscribe('message', self.handle)

    def handle(self, ev, msg):
        self.received.append(msg)

class DispatcherTest(unittest.TestCase):
    def test(self):
        e = MockEndpoint('node')
        d = Dispatcher(e)

        hfb = d.addEndpoint('foo/bar')
        lfb = Listener(hfb)

        hf = d.addEndpoint('foo')
        lf = Listener(hf)

        h = d.addEndpoint('')
        l = Listener(h)

        bm_to_fred = {'pcol': 'json', 'message': '{"o": "fred"}'}
        e.notify('message', bm_to_fred)

        self.assertEqual(l.received, [bm_to_fred])
        self.assertEqual(lf.received, [])
        self.assertEqual(lfb.received, [])

        msg_to_ffred = {'pcol': 'serf', 'message': encodes('foo/fred')}
        e.notify('message', msg_to_ffred)

        self.assertEqual(l.received, [bm_to_fred])
        self.assertEqual(lf.received, [msg_to_ffred])
        self.assertEqual(lfb.received, [])

        msg_to_fbb = {'pcol': 'serf', 'message': encodes('foo/bar/baz')}
        e.notify('message', msg_to_fbb)

        self.assertEqual(l.received, [bm_to_fred])
        self.assertEqual(lf.received, [msg_to_ffred])
        self.assertEqual(lfb.received, [msg_to_fbb])

        msg_to_fbark = {'pcol': 'serf', 'message': encodes('foo/bark')}
        e.notify('message', msg_to_fbark)

        self.assertEqual(l.received, [bm_to_fred])
        self.assertEqual(lf.received, [msg_to_ffred, msg_to_fbark])
        self.assertEqual(lfb.received, [msg_to_fbb])

if __name__ == '__main__':
    unittest.main()
