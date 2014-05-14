#!/usr/bin/python

"""Tests for the idl_types module."""

import unittest
from cStringIO import StringIO
from serf.idl_parser import *
from serf import idl_types

addParseActions(idl_types)

class IDLTypesTest(unittest.TestCase):
    def test(self):
        ex_prx = typeDef.parseString('Example*')[0]
        self.assertEqual(ex_prx, idl_types.ProxyType('Example'))

    def testParseExceptionDef(self):
        ex = exceptionDef.parseString('exception BadId { int id; };')[0]
        self.assertEqual(ex.cls, 'BadId')
        self.assertEqual(type(ex.member_list[0]), idl_types.Member)

if __name__ == '__main__':
    unittest.main()
