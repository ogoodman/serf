#!/usr/bin/python

"""Tests for BoundMethod."""

import unittest
from serf.serializer import encodes, decodes
from serf.bound_method import JCBoundMethod
from serf.mock_net import MockNet

class BoundMethodTest(unittest.TestCase):
    def test(self):
        net = MockNet()
        ls, lrpc = net.addRPCHandler('server', '', {})
        bs, brpc = net.addRPCHandler('browser', '', {})

        # Server one-way call.
        ls['obj'] = {'key': 'value'}
        set = JCBoundMethod(lrpc, 'obj', '__setitem__', 'server')
        set('key', 'new')
        self.assertEquals(ls['obj']['key'], 'new')

        # Browser one-way call.
        bs['obj'] = {'name': 'Fred'}
        bset = JCBoundMethod(lrpc, 'obj', '__setitem__', 'browser')
        self.assertEquals(bset('name', 'Ginger'), None)
        self.assertEquals(bs['obj']['name'], 'Ginger')

        # Should be able to send the bound method itself.
        bset('name', bset)
        b_bset = bs['obj']['name']
        self.assertEquals(type(b_bset), JCBoundMethod)
        # NOTE: really transported, not just ref to same.
        self.assertEquals(b_bset.handler(), brpc)

        del net, ls, lrpc, bs, brpc
        self.assertEquals(bset('name', 'Barney'), False)

if __name__ == '__main__':
    unittest.main()
