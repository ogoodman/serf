#!/usr/bin/python

"""Tests for SegmentedLog."""

import unittest
from segmented_log import SegmentedLog

class MockLogFile(object):
    def __init__(self, begin=0, data=None):
        self.data = [] if data is None else data
        self._begin = begin
        self._end = begin + len(self.data)

    def __getitem__(self, i):
        if i < self._begin or i >= self._end:
            raise IndexError(i)
        return self.data[i - self._begin]

    def append(self, item):
        self.data.append(item)
        self._end += 1

    def begin(self):
        return self._begin

    def end(self):
        return self._end

class MockLogDir(object):
    def __init__(self):
        self.dir = {}

    def __getitem__(self, key):
        return self.dir[key]

    def __delitem__(self, key):
        del self.dir[key]

    def keys(self):
        return self.dir.keys()

    def addLogFile(self, key, begin=0):
        self.dir[key] = MockLogFile(begin=begin)

class SegmentedLogTest(unittest.TestCase):
    def setUp(self):
        self.day = 0
        self.count = 0

    def keyfn(self):
        return '%04d' % self.day

    def makeItem(self):
        item = 'item%d' % self.count
        self.count += 1
        return item

    def test(self):
        dir = MockLogDir()
        log = SegmentedLog(self.keyfn, dir=dir)
        num_per_day = [234, 20, 145, 78, 10, 95, 36, 44]
        for num in num_per_day:
            for i in xrange(num):
                log.append(self.makeItem())
            self.day += 1
        self.assertEqual(log.begin(), 0)
        self.assertEqual(log.end(), sum(num_per_day))
        self.assertEqual(log[300], 'item300')

        # Check reopened log looks the same.
        log = SegmentedLog(self.keyfn, dir=dir)
        self.assertEqual(log.begin(), 0)
        self.assertEqual(log.end(), sum(num_per_day))
        self.assertEqual(log[300], 'item300')

        log.removeBefore('0002') # remove days 0 and 1.
        self.assertEqual(log.begin(), 234+20)
        self.assertEqual(log.end(), sum(num_per_day))
        self.assertEqual(log[300], 'item300')
        self.assertRaises(IndexError, log.__getitem__, 244)

        # Reopen truncated log.
        log = SegmentedLog(self.keyfn, dir=dir)
        self.assertEqual(log.begin(), 234+20)
        self.assertEqual(log.end(), sum(num_per_day))
        self.assertEqual(log[350], 'item350')
        self.assertRaises(IndexError, log.__getitem__, 244)

        # Check it handles a non-monotone keyfn.
        an_index = self.count + 5
        an_item = 'item%d' % an_index
        self.day -= 2 # keyfn going backwards now.

        for i in xrange(10):
            log.append(self.makeItem())
        self.assertEqual(log[an_index], an_item)
        # items always go into highest keyed chunk
        self.assertEqual(log.find(an_index), '0007')

if __name__ == '__main__':
    unittest.main()
