#!/usr/bin/python

"""Tests for the Synchronous thread-model."""

import unittest
from fred.synchronous import Synchronous

class SynchronousTest(unittest.TestCase):
    def test(self):
        tm = Synchronous()
        items = []

        def second():
            items.append('second')

        def first():
            tm.call(second)
            items.append('first')

        tm.callFromThread(first) # no threading, same as call.
        self.assertEqual(items, ['second', 'first'])

    def testCallback(self):
        tm = Synchronous()
        items = []

        def second(cb):
            items.append('first')
            cb.success('third')
            items.append('second')

        def first():
            cb = tm.makeCallback()
            tm.call(second, cb)
            items.append(cb.wait()) # third
            items.append('fourth')

        tm.callFromThread(first)
        self.assertEqual(items, ['first', 'second', 'third', 'fourth'])

if __name__ == '__main__':
    unittest.main()
