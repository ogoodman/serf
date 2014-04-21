#!/usr/bin/python

"""Tests for group of references."""

import unittest
from serf.po.group import Group

class TestObject(object):
    def __init__(self, can_throw=False):
        self.calls = 0
        self.can_throw = can_throw

    def foo(self, arg):
        self.calls += 1
        if not self.can_throw:
            return
        if arg == 'bad-value':
            raise ValueError(arg)
        if arg == 'bad-key':
            raise KeyError(arg)

class GroupTest(unittest.TestCase):
    def setUp(self):
        self.errors = []

    def errh(self, m, name, args, e):
        self.errors.append((m, name, args, e))

    def testAddRemove(self):
        group = Group()
        obj = TestObject()
        group._add(obj)

        group.foo('hi')
        self.assertEqual(obj.calls, 1)

        self.assertTrue(bool(group))

        # adding again is no-op
        group._add(obj)

        group.foo('hi')
        self.assertEqual(obj.calls, 2) # only one new call

        group._remove(obj)
        group.foo('hi')

        self.assertEqual(obj.calls, 2) # not called again

        group._remove(obj) # no problem to remove nonexistent

        self.assertFalse(bool(group))

    def testMultiple(self):
        o1 = TestObject(can_throw=True)
        o2 = TestObject()
        group = Group([o1, o2], errh=self.errh, fatal=[ValueError])

        group.foo('one')
        self.assertEqual(o1.calls, 1)
        self.assertEqual(o2.calls, 1)
        self.assertEqual(len(self.errors), 0)

        # by default AttributeErrors go to handler (not fatal)
        group.bar('two')
        self.assertEqual(o1.calls, 1)
        self.assertEqual(o2.calls, 1)
        self.assertEqual(len(self.errors), 2)
        self.assertEqual(type(self.errors[-1][-1]), AttributeError)

        # non-fatal exception, both still called, errors go to handler
        group.foo('bad-key')
        self.assertEqual(o1.calls, 2) # this one threw
        self.assertEqual(o2.calls, 2) # this one still called
        self.assertEqual(len(self.errors), 3)
        self.assertEqual(type(self.errors[-1][-1]), KeyError)

        # both still in group
        group.foo('ok')
        self.assertEqual(o1.calls, 3)
        self.assertEqual(o2.calls, 3)

        # fatal exception removes member
        group.foo('bad-value')
        self.assertEqual(o1.calls, 4) # this one threw
        self.assertEqual(o2.calls, 4) # this one still called
        self.assertEqual(len(self.errors), 4)
        self.assertEqual(type(self.errors[-1][-1]), ValueError)

        group.foo('more')
        self.assertEqual(o1.calls, 4) # this one was removed
        self.assertEqual(o2.calls, 5)
        self.assertEqual(len(self.errors), 4) # no new errors

if __name__ == '__main__':
    unittest.main()
