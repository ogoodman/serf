#!/usr/bin/python

"""Tests for the Worker thread-model."""

import threading
import unittest
from serf.worker import Worker
from serf.test_handler import TestHandler

class WorkerTest(unittest.TestCase):
    def test(self):
        worker = Worker()
        worker.start()

        cb = worker.makeCallback()
        th = TestHandler()

        def waitForCallback():
            th.handle('message', cb.wait())

        # callFromThread is same as call, both are thread-safe.
        worker.callFromThread(waitForCallback)

        with th.expect(1):
            cb.success(42)
        self.assertEqual(th.received, [42])


if __name__ == '__main__':
    unittest.main()
