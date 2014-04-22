#!/usr/bin/python

"""Tests for class Proxy."""

import unittest
from serf.mock_net import MockNet
from serf.vat import Vat
from serf.test_object import TestObject
from serf.proxy import Proxy


class ProxyTest(unittest.TestCase):
    def testFuture(self):
        net = MockNet()
        na = net.addVat('A', '1', {})
        nb = net.addVat('B', '1', {})

        pr = na.rpc.provide('addr', TestObject())
        ob = na.cache['addr']

        f = pr.incr_f(1) # remote call increment
        self.assertEqual(f.wait(), 2)

        f = pr.incr_f('x') # wrong argument type returns exception
        self.assertRaises(TypeError, f.wait)

        f = pr.foo_f()
        self.assertRaises(AttributeError, f.wait)

        pb = nb.rpc.provide('addrb', TestObject())

        pr.setProxy_f(pb) # pass pb to ob.
        self.assertNotEqual(ob.proxy, None)

        f = pr.callIncr_f(2) # get object at pb to increment
        self.assertEqual(f.wait(), 3)

    def testProxy(self):
        net = MockNet()
        na = net.addVat('A', '1', {})
        nb = net.addVat('B', '1', {})

        pr = na.rpc.provide('addr', TestObject())
        ob = na.cache['addr']

        self.assertEqual(pr.incr(1), 2) # remote call increment

        # wrong argument type returns exception
        self.assertRaises(TypeError, pr.incr, 'x')

        # NOTE: attribute error occurs only when called.
        self.assertRaises(AttributeError, pr.foo)

        pb = nb.rpc.provide('addrb', TestObject())

        pr.setProxy(pb) # pass pb to ob.
        self.assertNotEqual(ob.proxy, None)

        # get object at pb to increment
        self.assertEqual(pr.callIncr(2), 3)

    def testProxyEquality(self):
        va0 = Vat('A', '0', {})
        va1 = Vat('A', '1', {})
        vb0 = Vat('B', '0', {})
        p1 = Proxy('B', 'x', va0)
        p2 = Proxy('B', 'y', va1)
        p3 = Proxy('B', 'y', va0)
        p4 = Proxy('A', 'x', vb0)
        p5 = Proxy('A', 'y', vb0)
        p6 = Proxy('A', 'y', vb0)

        self.assertNotEqual(p1, p2)
        self.assertEqual(p2, p3) # only node and path are compared
        self.assertNotEqual(p1, p3)
        self.assertNotEqual(p1, p4)
        self.assertNotEqual(p3, p4)
        self.assertEqual(p5, p6)

if __name__ == '__main__':
    unittest.main()
