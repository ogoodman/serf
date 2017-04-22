#!/usr/bin/python

"""Tests for OnlineList."""

import unittest
from online_list import OnlineList
from player_list import PlayerList

class TestEntity(object):
    pass

class TestFactory(object):
    def make(self):
        return TestEntity()

    def init(self, online_list):
        self.online_list = online_list

class OnlineListTest(unittest.TestCase):
    def test(self):
        f = TestFactory()
        oll = OnlineList(f)

        events = []
        def onEvent(ev, info):
            events.append([ev, info])
        oll.subscribe('online', onEvent)
        oll.subscribe('offline', onEvent)

        addr = ('192.168.1.3', 32243)
        e = oll.add(addr)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[-1], ['online', [addr, e]])

        self.assertEqual(dict(oll.items()), {addr: e})

        oll.remove(addr)

        self.assertEqual(len(events), 2)
        self.assertEqual(events[-1], ['offline', [addr, e]])


if __name__ == '__main__':
    unittest.main()
