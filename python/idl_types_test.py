#!/usr/bin/python

"""Tests for the idl_types module."""

import unittest
from cStringIO import StringIO
from serf.idl_parser import *
from serf.idl_types import *

addParseActions()

class TestBuffer(object):
    def __init__(self):
        self.buffer = StringIO()
    def write(self, data):
        self.buffer.write(data)
    def writeln(self, data):
        self.buffer.write(data)
    def getvalue(self):
        return self.buffer.getvalue()

class IDLTypesTest(unittest.TestCase):
    def test(self):
        ex_prx = typeDef.parseString('Example*')[0]
        self.assertEqual(ex_prx, ProxyType('Example'))

    def testWriteCppInitArg(self):
        buf = TestBuffer()
        IDLType('var').writeCppInitArg(buf, 0)
        self.assertEqual(buf.getvalue(), 'serf::Var a0(args.at(0));')

if __name__ == '__main__':
    unittest.main()
