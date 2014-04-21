#!/usr/bin/python

"""Tests for traverse module."""

import unittest
from traverse import traverse

class TraverseTest(unittest.TestCase):
    def test(self):
        def fn(n):
            if n == 2:
                return 3
        self.assertEquals(traverse(2, fn), 3)
        self.assertEquals(traverse([1,2,3], fn), [1,3,3])
        self.assertEquals(traverse({'t':1, 'd':2}, fn), {'t':1, 'd':3}) 

if __name__ == '__main__':
    unittest.main()
