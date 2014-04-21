#!/usr/bin/python

"""Tests for EventletThread."""

import unittest
from fred.test_handler import TestHandler
from fred.eventlet_thread import EventletThread
from fred.eventlet_test_handler import TestHandler as EventletTestHandler

class EventletThreadTest(unittest.TestCase):
    def test(self):
        th = TestHandler()
        eth = EventletTestHandler()

        thread = EventletThread()
        thread.start()

        with eth.expect(1):
            thread.callFromThread(eth.handle, 'message', 'hi')

        thread.stop()
        thread.start(True) # now in a different thread

        with th.expect(1):
            thread.callFromThread(th.handle, 'message', 'lo')


if __name__ == '__main__':
    unittest.main()
