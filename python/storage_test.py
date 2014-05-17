#!/usr/bin/python

"""Tests for Storage."""

import unittest
from serf.util import EqualityMixin, Capture
from serf.storage import Storage, fcat, _str, NoSuchName
from serf.po.data import Data
from serf.ref import Ref
from serf.test_person import Person
from serf.test_time import Time
from serf.serializer import SerializationError, Record, encodes

class TestObject(EqualityMixin):
    serialize = ('data', 'obs')

    def __init__(self, data, obs):
        self.data = data
        self.obs = obs


class StorageTest(unittest.TestCase):
    def test(self):
        s = Storage({})

        s['a'] = TestObject({'name': 'Fred'}, [TestObject('sub', [])])

        s.clearCache()
        o = s['a']

        del o.ref # breaks equality so have to remove first.

        self.assertEqual(
            o, TestObject({'name': 'Fred'}, [TestObject('sub', [])]))

    def testData(self):
        store = Storage({})
        store['people/data/tom'] = Data({})
        t_data = store['people/data/tom']
        t_data['name'] = 'Tom'
        t_data['age'] = 14

        self.assertEqual(t_data['name'], 'Tom')

        env = Ref(store, 'people/data/tom')

        store['people/obj/tom'] = Person(env)
        tom = store['people/obj/tom']
        self.assertEqual(tom.description(), 'Tom age 14')
        tom.haveBirthday()
        self.assertEqual(t_data['age'], 15)

        store['people/data/gary'] = Data({})
        g_data = store['people/data/gary']
        g_data['name'] = 'Gary'
        g_data['age'] = 48
        t_data['dad'] = g_data

        self.assertEqual(type(t_data['dad']), Ref)

        self.assertEqual(tom.dadsName(), 'Gary')

        with Capture() as c:
            fcat(tom)
            self.assertEqual(c.getvalue(), "Person(env=ref(path='people/data/tom'))\n")

        # We can store refs anywhere in data. A top-level Data object
        # which has come from the store can turn itself into a ref.
        g_data['kids'] = [t_data]
        self.assertEqual(type(g_data['kids'][0]), Ref)
        self.assertEqual(g_data['kids'][0]['name'], 'Tom')

        # We do not support deep references into data (e.g. g_data['kids'])
        # because they would be very breakable, and copying would upset
        # the normal language expectation of node sharing.
        self.assertRaises(
            ValueError, t_data.__setitem__, 'siblings', g_data['kids'])

        store['caps/time'] = Time()
        t_data['time'] = store.getRef('caps/time')

        self.assertEqual(type(store['caps/time']), Time)
        self.assertEqual(type(t_data['time']), Ref)

        self.assertEqual(tom.whatTime(), 'Tea-time')

        t_data.save()
        g_data.save()

        store.clearCache()

        t_data = store['people/data/tom']
        g_data = store['people/data/gary']
        tom = store['people/obj/tom']

        self.assertEqual(t_data['name'], 'Tom')
        self.assertEqual(t_data['age'], 15)
        self.assertEqual(type(t_data['time']), Ref)
        self.assertEqual(t_data['time'].time(), 'Tea-time')

        tom.haveBirthday()

        self.assertEqual(g_data['kids'][0]['age'], 16)

    def testStoreAgainMakesRef(self):
        store = Storage({})
        data = Data({})
        store['a'] = data
        self.assertEqual(type(store['a']), Data)
        store['aref'] = data
        self.assertEqual(type(store['aref']), Ref)

        a = store['a']
        a['foo'] = 42
        self.assertEqual(store['aref']['foo'], 42)
        a.save()

        store.clearCache()
        self.assertEqual(type(store['a']), Data)
        self.assertEqual(type(store['aref']), Ref)
        self.assertEqual(store['a']['foo'], 42)

    def testUnnesting(self):
        store = Storage({})
        data = Data({})
        person = Person(data)

        store['person_data'] = data
        store['person'] = person

        del store.cache['person']
        self.assertEqual(type(store['person'].env), Ref)

    def testNames(self):
        vat = Storage({})
        foo = vat.makeRef(Data({}))

        foo['x'] = 'bar'
        vat.setn('foo', foo)

        foo1 = vat.getn('foo')
        self.assertEqual(foo1['x'], 'bar')

        # Can do it all in one..
        vat.setn('time', Time())
        self.assertEqual(vat.getn('time').time(), 'Tea-time')
        vat.getn('time')._erase()
        vat.deln('time')

    def testRefEquality(self):
        v = Storage({})
        ra1 = v.getRef('a')
        ra2 = v.getRef('a')
        rb = v.getRef('b')

        self.assertEqual(ra1, ra2)
        self.assertNotEqual(ra1, rb)

    def testSerializationErrors(self):
        proxy_enc = encodes(Record('ref', {'path':'p', 'node':'n'}))
        unk_enc = encodes(Record('unknown', 3))
        msg_enc = encodes(Record('@', 'xyz', 35))
        s = Storage({'caps/foo': proxy_enc, 'caps/unk': unk_enc, 'caps/msg': msg_enc})
        self.assertRaises(SerializationError, s.__getitem__, 'foo')
        self.assertRaises(SerializationError, s.__getitem__, 'unk')

        self.assertEqual(s['msg'], Record('@', 'xyz', 35))

        class NoSer(object):
            pass
        self.assertRaises(SerializationError, s.__setitem__, 'nos', NoSer())
        
        self.assertRaises(NoSuchName, s.getn, 'bimbo')

if __name__ == '__main__':
    unittest.main()
