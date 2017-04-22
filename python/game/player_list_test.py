#!/usr/bin/python

"""Tests for PlayerList."""

import unittest
from online_list import OnlineList
from player_list import PlayerList

class PlayerListTest(unittest.TestCase):
    def test(self):
        pl = PlayerList()
        oll = OnlineList(pl)

        pl_ev = []
        def onPEvent(ev, info):
            pl_ev.append([ev, info])
        pl.subscribe('online', onPEvent)
        pl.subscribe('offline', onPEvent)

        addr = ('192.168.1.3', 32243)
        p1 = oll.add(addr)

        self.assertEqual(len(pl_ev), 0) # don't know about Fred yet.

        p1.setName('Fred')

        self.assertEqual(len(pl_ev), 1)
        self.assertEqual(pl_ev[-1][0], 'online')
        self.assertEqual(pl_ev[-1][1][-1], 'Fred')
        fred_id = pl_ev[-1][1][0]

        self.assertEqual(pl.getPlayers().values(), ['Fred'])
        self.assertEqual(pl.getPlayer('Fred'), p1)
        self.assertEqual(pl.getPlayer('Barney'), None)

        oll.remove(addr)

        self.assertEqual(len(pl_ev), 2)

        self.assertEqual(pl_ev[-1][-1], fred_id)


if __name__ == '__main__':
    unittest.main()
