#!/usr/bin/python

"""Tests for the serialize module."""

import unittest
from fred.serialize import encodes, decodes
from fred.util import EqualityMixin


class A(EqualityMixin):
    def __init__(self, data):
        self.data = data

class TestContext(object):
    def encode(self, a, lev):
        return 'A', a.data
    def decode(self, name, data, lev):
        assert(name == 'A')
        return A(data)

class SerializeTest(unittest.TestCase):
    def test(self):
        def ed(value):
            return decodes(encodes(value))

        self.assertEqual(ed(None), None)
        self.assertEqual(ed(False), False)
        self.assertEqual(ed(True), True)
        self.assertEqual(ed(42), 42)
        self.assertEqual(ed(-30), -30)
        self.assertEqual(ed(1234567890000), 1234567890000)
        self.assertEqual(ed('some\x05binary'), 'some\x05binary')
        self.assertEqual(ed(u'Tom Brown'), u'Tom Brown')
        self.assertEqual(type(ed(u'Fred')), unicode)
        self.assertEqual(ed(3.14), 3.14)
        self.assertEqual(ed([None, True, False, 1, u'Hi', 3.14]),
                         [None, True, False, 1, u'Hi', 3.14])
        self.assertEqual(ed({'none': None, 't': True, 'one': 1, 'hi': u'Hi'}),
                         {'none': None, 't': True, 'one': 1, 'hi': u'Hi'})

    def testContext(self):
        ctx = TestContext()
        def ed(value):
            return decodes(encodes(value, ctx.encode), ctx.decode)

        self.assertEqual(ed(A(None)), A(None))
        self.assertEqual(ed(A([1,2,A(3)])), A([1,2,A(3)]))


if __name__ == '__main__':
    unittest.main()
