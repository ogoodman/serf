#!/usr/bin/python

"""Tests for LogFile."""

import os
import unittest
from fred.po.file import TestFile
from fred.po.log_file import LogFile

class LogFileTest(unittest.TestCase):
    def setUp(self):
        self.count = 0

    def makeItem(self):
        item = 'item%d' % self.count
        self.count += 1
        return item

    def test(self):
        f = TestFile()
        log = LogFile(f, bm_gap=8)

        self.assertEqual(log.begin(), 0)
        self.assertEqual(log.end(), 0)

        for i in xrange(300):
            log.append(self.makeItem())

        self.assertEqual(log.begin(), 0)
        self.assertEqual(log.end(), 300)
        self.assertEqual(log[123], 'item123')
        self.assertRaises(IndexError, log.__getitem__, -1)
        self.assertRaises(IndexError, log.__getitem__, 300)

        self.assertEqual(log[7:9], ['item7', 'item8'])
        self.assertEqual(log[8:6], [])
        self.assertEqual(log[299:304], ['item299'])
        self.assertEqual(log[-2:2], ['item0', 'item1'])

        log = LogFile(f, bm_gap=8)

        self.assertEqual(log.begin(), 0)
        self.assertEqual(log.end(), 300)

        self.assertEqual(log[59], 'item59')

        for i in xrange(100):
            log.append(self.makeItem())

        self.assertEqual(log[399], 'item399')
        log.append(self.makeItem())
        self.assertEqual(log[400], 'item400')

    def testNonzeroBegin(self):
        log = LogFile(TestFile(), begin=400)

        self.assertEqual(log.begin(), 400)
        self.assertEqual(log.end(), 400)

        self.count = 400 # so item name matches index
        for i in xrange(300):
            log.append(self.makeItem())

        self.assertEqual(log.begin(), 400)
        self.assertEqual(log.end(), 700)
        self.assertEqual(log[523], 'item523')
        self.assertRaises(IndexError, log.__getitem__, 399)
        self.assertRaises(IndexError, log.__getitem__, 700)

        self.assertEqual(log[398:402], ['item400', 'item401'])


if __name__ == '__main__':
    unittest.main()
