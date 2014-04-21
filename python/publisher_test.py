#!/usr/bin/python

"""Tests for publisher module."""

import unittest
import weakref
from publisher import Publisher

class Parent(object):
    def __init__(self, child):
        self.child = child
        self.child.subscribe('event', self.onEvent)
        self.from_child = None

    def onEvent(self, event, info):
        self.from_child = info

class PublisherTest(unittest.TestCase):
    def testNonCyclic(self):
        # Publishers are supposed to break cyclic dependencies; we have
        # two-way communication between parent and child without the
        # child holding a reference to the parent.
        p = Parent(Publisher())

        p.child.notify('event', 'foo')
        p.child.notify('event', 'bar')
        self.assertEqual(p.from_child, 'bar')

        wp = weakref.ref(p)
        self.assertTrue(wp() is not None)
        del p
        self.assertTrue(wp() is None)

if __name__ == '__main__':
    unittest.main()
