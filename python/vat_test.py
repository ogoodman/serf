#!/usr/bin/python

"""Tests for class Vat."""

import unittest
from fred.vat import Vat, convert
from fred.mock_net import MockNet
from fred.proxy import Proxy
from fred.ref import Ref
from fred.po.data import Data
from fred.test_object import TestObject
from fred.serialize import SerializationError
from fred.test_time import Time
from fred.green_thread import GreenThread
from fred.worker import Worker
from fred.test_handler import TestHandler
from fred.eventlet_thread import EventletThread
from fred.storage import Storage

class VatTest(unittest.TestCase):
    def testCall(self):
        net = MockNet()
        nodea = net.addVat('A', '1', {})
        nodeb = net.addVat('B', '1', {})

        nodea['addr'] = TestObject()

        cb = nodeb.rpc.call('A', 'addr', 'incr', [1])

        self.assertEqual(cb.result, 2)

    def testWithStorage(self):
        net = MockNet()
        na = net.addVat('A', '1', {})
        nb = net.addVat('B', '1', {})

        na['TOB'] = Data({}) # store a data object

        # call it from node b
        c1 = nb.rpc.call('A', 'TOB', '__setitem__', ['foo', 1])
        c2 = nb.rpc.call('A', 'TOB', 'save', [])

        # simulate restart of node a
        na.clearCache()

        # retrieve saved value from node a
        c3 = nb.rpc.call('A', 'TOB', '__getitem__', ['foo'])
        self.assertEqual([c1.wait(), c2.wait(), c3.wait()], [None, None, 1])

    def testNonexistentNode(self):
        net = MockNet()
        na = net.addVat('A', '0', {})
        cb = na.rpc.call('B', 'x', 'method', [])
        self.assertRaises(KeyError, cb.wait)

    def test(self):
        net = MockNet()
        na = net.addVat('A', '1', {})
        nb = net.addVat('B', '1', {})

        na['a'] = Time()
        na['o'] = TestObject()

        na.clearCache()

        nb['ap'] = nb.makeProxy('a', 'A')
        nb['op'] = nb.makeProxy('o', 'A')
        nb['d'] = Data({'name': u'Fred'})
        nb['b'] = Time()
        nb['br'] = nb.getRef('b')

        b = nb['b']
        self.assertEqual(type(b), Time)
        br = nb['br']
        self.assertEqual(type(br), Ref)
        ap = nb['ap']
        self.assertEqual(type(ap), Proxy)
        d = nb['d']
        self.assertEqual(type(d), Data)

        # This activity is all on node B calling through to node A.
        op = nb['op']
        op.setProxy(ap) # ap is a Proxy
        self.assertEqual(op.callTime(), 'TestObject.callTime: Tea-time')
        #op.setProxy(b) # b is a Time capability
        #op.callTime()
        op.setProxy(br) # br is a Ref
        op.callTime()
        op.setProxy(d) # d is a Data
        op.setName(u'Barney')

        self.assertEqual(d['name'], u'Barney')

    def testAddVat(self):
        net = MockNet()
        va = net.addVat('A', '1', {})
        vb1 = net.addVat('B', '1', {})
        vb2 = net.addVat('B', '2', {})

        va['df'] = {'name': u'Fred'}
        vb2['db'] = {'name': u'Barney'}

        p = vb1.makeProxy('df', 'A')
        p2 = vb1.makeProxy('db', 'B')

        self.assertEqual(p['name'], u'Fred')
        self.assertEqual(p2['name'], u'Barney')

        self.assertEqual(net.node['A'].getVatId('df'), '1')

        self.assertEqual(type(vb1['db']), Proxy)
        self.assertEqual(type(vb2['db']), dict)

    def testGreen(self):
        net = MockNet()
        gta = GreenThread()
        va = net.addVat('X', 'A', {}, t_model=gta)
        gta.start()

        gtb = GreenThread()
        vb = net.addVat('X', 'B', {}, t_model=gtb)
        gtb.start()

        va['data'] = {'name': 'Tom'}

        pb = vb.makeProxy('data', 'X')

        th = TestHandler()

        def pr(fn, arg):
            th.handle('message', fn(arg))

        # The reason we have to call pa[] in gta (green thread a)
        # is because if the cb.wait() is called by this thread
        # cb.main_loop and cb.resume end up being in different threads.

        with th.expect(1):
            gtb.callFromThread(pr, pb.__getitem__, 'name')
        self.assertEqual(th.received, ['Tom'])

        gta.stop()
        gtb.stop()

    def testWorker(self):
        net = MockNet()
        gta = EventletThread()
        va = net.addVat('X', 'A', {}, t_model=gta)
        gta.start(True)

        worker = EventletThread()
        vb = net.addVat('X', 'B', {}, t_model=worker)
        worker.start()

        va['data'] = {'name': 'Tom'}

        pb = vb.makeProxy('data', 'X')
        self.assertEqual(pb['name'], 'Tom')

    def testMultipleVats(self):
        net = MockNet()
        store = {}
        v1 = net.addVat('N', '1', store)
        v2 = net.addVat('N', '2', store)
        node = net.node['N']

        p = v1.makeRef({'a': 1}, vat_id='2') # make new object in different vat.
        self.assertFalse(p._path in v1.cache)
        r = convert(v1.rpc, v2.rpc, p)
        self.assertEqual(type(r), Ref)
        self.assertEqual(p['a'], 1)
        self.assertEqual(node.getVatId(p._path), '2')

if __name__ == '__main__':
    unittest.main()
