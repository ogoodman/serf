#!/usr/bin/python

"""Test for functions in serf.util."""

import unittest
import sys
from serf.util import EqualityMixin, rmap, Capture, getOptions, timeCall

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
    
        self.assertTrue(A(1) != A(2))

    def testCapture(self):
        with Capture() as c:
            print 'not printed'
            self.assertEquals(c.getvalue(), 'not printed\n')

    def testGetOptions(self):
        self.exit_called = False
        def exit():
            self.exit_called = True
        def helpfn():
            print 'help'
        try:
            keep_args = sys.argv
            keep_exit = sys.exit
            sys.argv = 'prog.py -r -x x1 -x xopt tom dick'.split()
            sys.exit = exit
            opt, args = getOptions('rx:y:', [])
            self.assertEqual(args, ['tom', 'dick'])
            self.assertTrue(opt('-r'))
            self.assertEquals(opt('-x'), 'xopt')
            self.assertEquals(opt('-y'), None)
            self.assertEquals(opt('-x', all=True), ['x1', 'xopt'])

            sys.argv = 'prog.py -h'.split()
            with Capture() as c:
                opt, args = getOptions('h', ['help'])
                self.assertEquals(c.getvalue().strip(), __doc__)
            sys.argv = 'prog.py --what'.split()
            with Capture() as c:
                opt, args = getOptions('h', ['help'], 'DOCS')
                self.assertEquals(c.getvalue().strip(), 'DOCS')
            sys.argv = 'prog.py --help'.split()
            with Capture() as c:
                opt, args = getOptions('h', ['help'], helpfn)
                self.assertEquals(c.getvalue().strip(), 'help')
            self.assertTrue(self.exit_called)

        finally:
            sys.argv = keep_args
            sys.exit = keep_exit

    def testTimeCall(self):
        def fun(a):
            pass
        with Capture() as c:
            timeCall(fun, 'a')
            float(c.getvalue().strip()) # does not throw.

if __name__ == '__main__':
    unittest.main()

