#!/usr/bin/python

"""Test for functions in serf.util."""

import unittest
from serf.util import EqualityMixin, rmap

class A(EqualityMixin):
    def __init__(self, arg):
        self.arg = arg

class B(EqualityMixin):
    def __init__(self, arg):
        self.arg = arg

def convAtoB(a):
    return B(a.arg)

def convert(x):
    typ = type(x)
    if typ in (int, long, str, unicode):
        return x
    if typ is A:
        return convAtoB(x)

def conv(info):
    return rmap(convert, info)

class UtilTest(unittest.TestCase):
    def test(self):
        self.assertEqual(A('foo'), A('foo'))
        self.assertEqual(conv(1), 1)
        self.assertEqual(conv([1]), [1])
        b = conv(A('foo'))
        self.assertEqual(b.__class__, B)
        self.assertEqual(b.arg, 'foo')
        self.assertEqual(conv({'a': 1, 'b': A('foo')}), {'a': 1, 'b':B('foo')})
        self.assertEqual(conv((u'x', A(2))), (u'x', B(2)))


if __name__ == '__main__':
    unittest.main()

