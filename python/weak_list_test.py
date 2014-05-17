#!/usr/bin/python

"""Tests for weak_list module."""

import unittest
from weak_list import WeakList

class A(object):
    def foo(self):
        pass

class CB(object):
    def __call__(self):
        pass

class WeakListTest(unittest.TestCase):
    def testMethod(self):
        l = WeakList()
        a = A()
        l.add(a)
        self.assertEqual(len(l), 1)
        self.assertTrue(a in l.items())
        del a
        self.assertEqual(len(l), 0)
        self.assertEqual(l.items(), [])

        a1 = A()
        l.add(a1.foo)
        self.assertEqual(len(l), 1)
        self.assertEqual(l.items()[0](), None)
        del a1
        self.assertEqual(len(l), 0)
        self.assertEqual(l.items(), [])

        a2 = A()
        l.add(a2.foo)
        self.assertEqual(len(l), 1)
        l.discard(a2.foo)
        self.assertEqual(len(l), 0)

    def testLambda(self):
        l = WeakList()
        c = lambda: None
        l.add(c)
        self.assertEqual(len(l), 1)
        self.assertEqual(l.items()[0](), None)
        del c
        self.assertEqual(len(l), 0)
        self.assertEqual(l.items(), [])

        d = lambda: None
        l.add(d)
        self.assertEqual(len(l), 1)
        l.discard(d)
        self.assertEqual(len(l), 0)

    def testClosure(self):
        def makeClosure():
            def func():
                pass
            return func
        c = makeClosure()
        l = WeakList()
        l.add(c)
        self.assertEqual(len(l), 1)
        self.assertEqual(l.items()[0](), None)
        del c
        self.assertEqual(len(l), 0)
        self.assertEqual(l.items(), [])

    def testCallable(self):
        c = CB()
        l = WeakList()
        l.add(c)
        self.assertEqual(len(l), 1)
        self.assertEqual(l.items()[0](), None)
        del c
        self.assertEqual(len(l), 0)
        self.assertEqual(l.items(), [])

if __name__ == '__main__':
    unittest.main()
