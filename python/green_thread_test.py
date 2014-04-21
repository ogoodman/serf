#!/usr/bin/python

"""Test of green threads."""

import unittest
from greenlet import greenlet
from green_thread import GreenThread, TSGreenThread
from test_handler import TestHandler

class GreenThreadTest(unittest.TestCase):
    def setUp(self):
        self.thread = GreenThread()
        self.thread.start()

    def tearDown(self):
        self.thread.stop()
        assert(not self.thread.items)

    def test(self):
        th = TestHandler()

        def second():
            th.handle('message', {'message': 'second'})

        def first():
            self.thread.call(second)
            th.handle('message', {'message': 'first'})

        with th.expect(2):
            self.thread.callFromThread(first)
        # NOTE: with a synchronous call, the order would be reversed.
        self.assertEqual(th.received, ['first', 'second'])

    def testCallback(self):
        th = TestHandler()

        def second(cb):
            th.handle('message', {'message': 'first'})
            cb.success('second')
            th.handle('message', {'message': 'fourth'})

        def first():
            cb = self.thread.makeCallback()
            self.thread.call(second, cb)
            th.handle('message', {'message': cb.wait()})
            th.handle('message', {'message': 'third'})

        with th.expect(4):
            self.thread.callFromThread(first)
        self.assertEqual(th.received, ['first', 'second', 'third', 'fourth'])

    def testSafeGreenThread(self):
        th = TestHandler()

        def callAndWait(thread):
            cb = thread.makeCallback()
            thread.call(cb.success, 'result')
            return cb.wait()

        self.assertRaises(greenlet.error, callAndWait, self.thread)
        self.thread.items = [] # Avoid assertion in tearDown.

        ts_green = TSGreenThread()
        ts_green.start()

        self.assertEqual(callAndWait(ts_green), 'result')

        ts_green.stop()
        self.assertEqual(ts_green.items, [])


if __name__ == '__main__':
    unittest.main()
