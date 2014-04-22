#!/usr/bin/python

"""Tests for NodeObserver."""

import unittest
import socket
from serf.po.node_observer import NodeObserver
from serf.synchronous import Synchronous

class TestObserver(object):
    def __init__(self):
        self.nodes = []

    def online(self, node):
        self.nodes.append(node)

class TestRef(object):
    def __init__(self):
        self.saved = 0

    def _save(self):
        self.saved += 1

class TestVat(object):
    def __init__(self):
        self.online = []
        self.thread_model = Synchronous()
        self.pinged = []
        self.node_observer = None

    def call(self, node, *rest):
        self.pinged.append(node)
        cb = self.thread_model.makeCallback()
        if node not in self.online:
            cb.failure(socket.error())
        else:
            cb.success(None)
            self.node_observer.connected(node)
        return cb

    def getRPC(self):
        return self

class NodeObserverTest(unittest.TestCase):
    def test(self):
        vat = TestVat()
        no = NodeObserver(vat)
        vat.node_observer = no
        no.ref = TestRef() # Normally added by Vat.__getitem__
        no._save = no.ref._save
        obs = TestObserver()

        no.addObserver('A', obs)
        no.ping('A') # A is not online yet.
        self.assertEqual(obs.nodes, [])
        self.assertEqual(no.ref.saved, 1)

        vat.online.append('A')
        no.ping('A')
        self.assertEqual(obs.nodes, ['A'])
        self.assertEqual(vat.pinged, ['A', 'A'])

        # If NodeObserver counts A as a peer it will check when it goes online.
        no.addPeer('A')
        no.addPeer('B')
        no.addObserver('B', obs)
        self.assertEqual(no.ref.saved, 4)
        no.online('me')
        self.assertEqual(obs.nodes, ['A', 'A']) # Nothing from B, not online.

        # Nodes 'A' and 'B' have been pinged and will know that 'me' is online.
        self.assertEqual(vat.pinged, ['A', 'A', 'A', 'B'])

        # If B has us as a peer it will call no.connected('B')
        vat.online.append('B') # NOTE: does not affect next call.
        no.connected('B')
        self.assertEqual(obs.nodes, ['A', 'A', 'B'])

        no.removeObserver('A', obs)

        # 'A' is still a peer, so we still ping it when we go online.
        no.online('me')
        self.assertEqual(vat.pinged, ['A', 'A', 'A', 'B', 'A', 'B'])
        self.assertEqual(obs.nodes, ['A', 'A', 'B', 'B'])

        no.removePeer('A')
        no.removePeer('B')

        # Now we only ping B because we want to observe it.
        no.online('me')
        self.assertEqual(len(vat.pinged), 7)
        self.assertEqual(obs.nodes, list('AABBB'))


if __name__ == '__main__':
    unittest.main()
