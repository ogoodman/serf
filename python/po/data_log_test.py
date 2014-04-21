#!/usr/bin/python

"""Tests for a DataLog."""

import unittest
from serf.storage import Storage
from serf.test_fs import TestFS
from serf.po.file import File
from serf.po.data_log import DataLog

class TestCallLog(object):
    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        def _log_call(*args):
            self.calls.append((name, args))
        return _log_call

class DataLogTest(unittest.TestCase):
    def test(self):
        v = Storage(TestFS())

        dl = DataLog(v, File(v, 'f'))
        v['dl'] = dl

        cl = TestCallLog()

        dl.append(1)
        self.assertEqual(dl.begin(), 0)
        self.assertEqual(dl.end(), 1)
        self.assertEqual(dl[0], 1)

        dl.addObserver(cl)
        dl.append('two')
        self.assertEqual(cl.calls, [('add', (1, 'two'))])

        dl.removeObserver(cl)
        dl.append({'three': 3})
        self.assertEqual(len(cl.calls), 1)

        self.assertEqual(dl.end(), 3)
        self.assertEqual(dl[1:3], ['two', {'three': 3}])

        v.clearCache()
        dl = v['dl']

        self.assertEqual(dl.end(), 3)
        self.assertEqual(dl[0:2], [1, 'two'])


if __name__ == '__main__':
    unittest.main()
