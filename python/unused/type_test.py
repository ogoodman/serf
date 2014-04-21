#!/usr/bin/python

"""Tests for Types."""

import unittest
from datetime import date
from serf.obj import obj
from type import Types, RefTypes
from mock_proxy import MockProxyFactory, Proxy, SProxy

class TypesTest(unittest.TestCase):
    def testTypes(self):
        types = Types().types # only one facet to test

        self.assertEqual(types.normalize(42, 'int'), 42)
        self.assertEqual(types.normalize(u'Tom', 'str'), u'Tom')
        self.assertEqual(type(types.normalize('Tom', 'str')), unicode)
        self.assertEqual(types.normalize(date(2009, 7, 18), 'date'), date(2009, 7, 18))

        self.assertRaises(TypeError, types.normalize, 35, 'str')
        self.assertRaises(TypeError, types.normalize, date(2009, 7, 18), 'int')
        self.assertRaises(TypeError, types.normalize, '18/7/2009', 'date')

        self.assertRaises(ValueError, types.normalize, 35, 'foo')

        self.assertEqual(types.denormalize(42, 'int'), 42)
        self.assertRaises(ValueError, types.denormalize, 'Fred', 'ref')

    def testRefTypes(self):
        types = RefTypes(obj(proxy_factory=MockProxyFactory())).types

        # As before.
        self.assertEqual(types.normalize(42, 'int'), 42)
        self.assertEqual(types.normalize(u'Tom', 'str'), u'Tom')
        self.assertEqual(type(types.normalize('Tom', 'str')), unicode)
        self.assertEqual(types.normalize(date(2009, 7, 18), 'date'), date(2009, 7, 18))

        self.assertRaises(TypeError, types.normalize, 35, 'str')
        self.assertRaises(TypeError, types.normalize, date(2009, 7, 18), 'int')
        self.assertRaises(TypeError, types.normalize, '18/7/2009', 'date')

        self.assertRaises(ValueError, types.normalize, 35, 'foo')

        self.assertEqual(types.denormalize(42, 'int'), 42)

        # Now ref is a known type but a str doesn't match.
        self.assertRaises(TypeError, types.denormalize, 'Fred', 'ref')

        self.assertEqual(types.normalize(Proxy('p1'), 'ref'), SProxy('p1'))
        self.assertEqual(types.denormalize(SProxy('p2'), 'ref'), Proxy('p2'))

if __name__ == '__main__':
    unittest.main()
