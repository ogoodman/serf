#!/usr/bin/python

"""Tests for Refs."""

import unittest
from fred.serialize import SerializationError
from fred.ref import Ref, ReferenceError
from fred.mock_net import MockNet
from fred.obj import obj
from fred.proxy import Proxy
from fred.test_data import TestData
from fred.storage import Storage

class RefTest(unittest.TestCase):
    def testFacets(self):
        data = TestData(14)
        vat = {'data': data}
        ref = Ref(vat, 'data', 'public')

        self.assertEqual(ref.get(), 14)
        self.assertRaises(AttributeError, getattr, ref, 'set')

        data.setMaster(True)

        ref.set(42)
        self.assertEqual(ref.get(), 42)

        self.assertRaises(ReferenceError, ref._save)
        self.assertRaises(ReferenceError, ref._erase)
        self.assertRaises(ReferenceError, ref._set, 'Anything')
        self.assertRaises(ReferenceError, ref._getFacet, 'nested')
        self.assertRaises(ReferenceError, Ref, vat, 'data', '_private')

    def testFacetRef(self):
        vat = Storage({})
        main_ref = vat.makeRef(TestData(24))
        public = vat.makeRef(main_ref._getFacet('public'))

        self.assertEqual(public.get(), 24)
        self.assertRaises(AttributeError, getattr, public, 'set')

        # main_ref references a TestData instance
        self.assertEqual(type(main_ref._get()), TestData)

        # public references a facet Ref
        self.assertEqual(type(public._get()), Ref)
        self.assertEqual(public._get()._facet, 'public')

        # the facet Ref references an obj instance
        self.assertEqual(type(public._get()._get()), obj)

        # check facet is not lost in serialization.
        public._close()
        self.assertEqual(public._get()._facet, 'public')

    def testFacetProxy(self):
        net = MockNet()
        va = net.addVat('A', '1', {})
        vb = net.addVat('B', '1', {})

        main_ref = va.makeRef(TestData(24))
        public = va.makeRef(main_ref._getFacet('public'))

        bdata = vb.makeRef(TestData())
        bproxy = va.rpc.makeProxy(bdata._path, 'B') # proxy for bdata in A.

        # To test serialization of the public facet we will
        # attempt to pass it to the remote object.

        bproxy.set(public) # NOTE: bdata is not a facet so get/set both work.

        # Check the proxy to facet-ref arrived OK.
        self.assertEqual(type(bdata.value), Proxy)

        # Check it is really a proxy to the facet.
        self.assertRaises(AttributeError, bproxy.doSet, 25)
        main_ref.setMaster(True) # switch to master and try again.
        bproxy.doSet(25)
        self.assertEqual(bdata.value.get(), 25)

        # NOTE: that we can't send a facet-ref directly because
        # that would reveal the slot path of the main object to the
        # remote user.
        self.assertRaises(SerializationError, bproxy.set, public._get())

if __name__ == '__main__':
    unittest.main()
