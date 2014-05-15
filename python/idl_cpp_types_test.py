#!/usr/bin/python

"""Tests for the C++ code-generating IDL types module."""

import unittest
from cStringIO import StringIO
from serf import idl_cpp_types as idl
from serf.util import IndentingStream

def capture(fn, *args):
    buf = StringIO()
    wrap = IndentingStream(buf)
    fn(wrap, *args)
    return buf.getvalue()

class IDLCppTypesTest(unittest.TestCase):
    def testFixAngleBrackets(self):
        lli = idl.IDLType('list', idl.IDLType('list', idl.IDLType('int')))
        self.assertEquals(lli.cppType(), 'std::vector<std::vector<int32_t> >')

    def testWriteCppInitArg(self):
        code = capture(idl.IDLType('var').writeCppInitArg, 0)
        self.assertEqual(code, 'serf::Var a0(args.at(0));\n')

        code = capture(idl.ProxyType('Example').writeCppInitArg, 0)
        self.assertEqual(code, 'ExamplePrx a0(rpc, boost::get<serf::Record const&>(args.at(0)));\n')

    def testWriteInitMember(self):
        int_mem = idl.Member(idl.IDLType('int'), 'x')
        self.assertEqual(capture(int_mem.writeInitMember),
                         'x = boost::get<int32_t>(M(value)["x"]);\n')
        intl = idl.IDLType('list', idl.IDLType('int'))
        intl_mem = idl.Member(intl, 'v')
        self.assertEqual(
            capture(intl_mem.writeInitMember), 'extract(v, M(value)["v"]);\n')

    def testExceptionDef(self):
        int_mem = idl.Member(idl.IDLType('int'), 'x')
        smap_mem = idl.Member(idl.IDLType('dict', idl.IDLType('ascii')), 'props')
        text_mem = idl.Member(idl.IDLType('text'), 'desc')
        exc = idl.ExceptionDef('MyBad', [int_mem, smap_mem, text_mem])
        print capture(exc.writeDecl)
        print capture(exc.writeDef),

if __name__ == '__main__':
    unittest.main()
