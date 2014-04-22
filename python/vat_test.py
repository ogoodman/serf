#!/usr/bin/python

"""Tests for class Vat."""

import unittest
import weakref
from serf.vat import Vat, convert
from serf.mock_net import MockNet
from serf.proxy import Proxy
from serf.ref import Ref
from serf.po.data import Data
from serf.test_object import TestObject
from serf.serialize import SerializationError
from serf.test_time import Time
from serf.green_thread import GreenThread
from serf.worker import Worker
from serf.test_handler import TestHandler
from serf.eventlet_thread import EventletThread
from serf.storage import Storage
from serf.json_codec import makeBoundMethod
from serf.publisher import Publisher
from serf.model import Model

class MockTransport(Publisher):
    client_ip = 'ip'
    node_id = 'browser'

    def send(self, node, message, errh=None):
        self.peer.notify('message', {'node': self.node_id, 'message': message})

class VatTest(unittest.TestCase):
    def testCall(self):
        net = MockNet()
        nodea, va = net.addVat('A', '1', {})
        nodeb, vb = net.addVat('B', '1', {})

        nodea['addr'] = TestObject()

        cb = vb.call('A', 'addr', 'incr', [1])

        self.assertEqual(cb.result, 2)

    def testWithStorage(self):
        net = MockNet()
        na, va = net.addVat('A', '1', {})
        nb, vb = net.addVat('B', '1', {})

        na['TOB'] = Data({}) # store a data object

        # call it from node b
        c1 = vb.call('A', 'TOB', '__setitem__', ['foo', 1])
        c2 = vb.call('A', 'TOB', 'save', [])

        # simulate restart of node a
        na.clearCache()

        # retrieve saved value from node a
        c3 = vb.call('A', 'TOB', '__getitem__', ['foo'])
        self.assertEqual([c1.wait(), c2.wait(), c3.wait()], [None, None, 1])

    def testNonexistentNode(self):
        net = MockNet()
        na, va = net.addVat('A', '0', {})
        cb = va.call('B', 'x', 'method', [])
        self.assertRaises(KeyError, cb.wait)

    def test(self):
        net = MockNet()
        na, va = net.addVat('A', '1', {})
        nb, vb = net.addVat('B', '1', {})

        na['a'] = Time()
        na['o'] = TestObject()

        na.clearCache()

        nb['ap'] = vb.makeProxy('a', 'A')
        nb['op'] = vb.makeProxy('o', 'A')
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
        va, ra = net.addVat('A', '1', {})
        vb1, rb1 = net.addVat('B', '1', {})
        #vb2, rb2 = net.addVat('B', '2', {})

        va['df'] = {'name': u'Fred'}
        vb1['db'] = {'name': u'Barney'}

        p = rb1.makeProxy('df', 'A')
        p2 = rb1.makeProxy('db', 'B')

        self.assertEqual(p['name'], u'Fred')
        self.assertEqual(p2['name'], u'Barney')

        self.assertEqual(net.node['A'].getVatId('df'), '1')

        self.assertEqual(type(vb1['db']), dict)
        #self.assertEqual(type(vb2['db']), dict)

    def testGreen(self):
        net = MockNet()
        gta = GreenThread()
        va, ra = net.addVat('X', 'A', {}, t_model=gta)
        gta.start()

        gtb = GreenThread()
        vb, rb = net.addVat('X', 'B', {}, t_model=gtb)
        gtb.start()

        va['data'] = {'name': 'Tom'}

        pb = rb.makeProxy('data', 'X')

        th = TestHandler()

        def pr(fn, arg):
            th.handle('message', {'message': fn(arg)})

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
        va, ra = net.addVat('X', 'A', {}, t_model=gta)
        gta.start(True)

        worker = EventletThread()
        vb, rb = net.addVat('X', 'B', {}, t_model=worker)
        worker.start()

        va['data'] = {'name': 'Tom'}

        pb = rb.makeProxy('data', 'X')
        self.assertEqual(pb['name'], 'Tom')

    def testGC(self):
        h = Vat('browser', '1', {}, Publisher())
        makeBoundMethod(h, {'o':'shared', 'm':'notify'})
        hr = weakref.ref(h)
        self.assertEqual(hr(), h)
        del h
        self.assertEqual(hr(), None)

    def testRPC(self):
        ta = MockTransport()
        tb = MockTransport()
        ta.peer = tb
        tb.peer = ta

        na = Vat('browser', '1', {}, ta)
        nb = Vat('browser', '2', {}, tb)

        oa = Model()
        na.provide(1, oa)

        rset = makeBoundMethod(nb, {'o':1, 'm':'set'})
        rset('x', 1)

        self.assertEqual(oa.get('x'), 1)

if __name__ == '__main__':
    unittest.main()
