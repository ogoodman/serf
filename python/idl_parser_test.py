#!/usr/bin/python

"""Tests for the idl_parser module."""

import unittest
from serf.idl_parser import *

class IDLParserTest(unittest.TestCase):
    def test(self):
        typeDef.parseString('list<int>')
        operationDef.parseString('void setProxy(in Example* ep);')
        exceptionDef.parseString('exception BadId { int id; };')

if __name__ == '__main__':
    unittest.main()
