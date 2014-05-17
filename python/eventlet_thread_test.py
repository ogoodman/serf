#!/usr/bin/python

"""Tests for EventletThread."""

import unittest
from serf.test_handler import TestHandler
from serf.eventlet_thread import EventletThread
from serf.eventlet_test_handler import TestHandler as EventletTestHandler

class EventletThreadTest(unittest.TestCase):
    def test(self):
        th = TestHandler()
        eth = EventletTestHandler()

        thread = EventletThread()
        thread.start()

        with eth.expect(1):
            thread.callFromThread(eth.handle, 'message', {'message': 'hi'})

        with eth.expect(1):
            thread.callAfter(0, eth.msg, 'foo')

        cb = thread.makeCallback()
        thread.callAfter(0, cb.failure, Exception('bar'))
        self.assertRaises(Exception, cb.wait)

        thread.stop()
        thread.start(True) # now in a different thread

        with th.expect(1):
            thread.callFromThread(th.handle, 'message', {'message': 'lo'})

        # NOTE: we don't stop it here. There should be an atexit handler
        # to do that for us. If that fails the tests will hang.

if __name__ == '__main__':
    unittest.main()
