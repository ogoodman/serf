#!/usr/bin/python

"""Tests for the C++ code-generating IDL types module."""

import unittest
from cStringIO import StringIO
from serf import idl_cpp_types as idl

class TestBuffer(object):
    def __init__(self):
        self.buffer = StringIO()
    def write(self, data):
        self.buffer.write(data)
    def writeln(self, data):
        self.buffer.write(data)
    def getvalue(self):
        return self.buffer.getvalue()
    def clear(self):
        self.buffer.truncate(0)

def capture(fn, *args):
    buf = TestBuffer()
    fn(buf, *args)
    return buf.getvalue()

class IDLCppTypesTest(unittest.TestCase):
    def testFixAngleBrackets(self):
        lli = idl.IDLType('list', idl.IDLType('list', idl.IDLType('int')))
        self.assertEquals(lli.cppType(), 'std::vector<std::vector<int32_t> >')

    def testWriteCppInitArg(self):
        code = capture(idl.IDLType('var').writeCppInitArg, 0)
        self.assertEqual(code, 'serf::Var a0(args.at(0));')

        code = capture(idl.ProxyType('Example').writeCppInitArg, 0)
        self.assertEqual(code, 'ExamplePrx a0(rpc, boost::get<serf::Record const&>(args.at(0)));')

    def testWriteInitMember(self):
        int_mem = idl.Member(idl.IDLType('int'), 'x')
        self.assertEqual(capture(int_mem.writeInitMember),
                         'x = boost::get<int32_t>(M(value)["x"]);')
        intl = idl.IDLType('list', idl.IDLType('int'))
        intl_mem = idl.Member(intl, 'v')
        self.assertEqual(
            capture(intl_mem.writeInitMember), 'extract(v, M(value)["v"]);')

if __name__ == '__main__':
    unittest.main()
