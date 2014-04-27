#!/usr/bin/env python

"""Tests for the serializer module."""

import unittest
from serializer import *

class Custom(object):
    def __init__(self, bar, baz):
        self.bar = bar
        self.baz = baz
    def __eq__(self, other):
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        return False
    def __str__(self):
        return 'Custom(%r,%r)' % (self.bar, self.baz)
    def get_state(self):
        return 'custom', [self.bar, self.baz]
    @staticmethod
    def construct(value):
        return Custom(value[0], value[1])

REG = Registry()

class SerializationTest(unittest.TestCase):
    def test(self):
        self.assertEqual(decodes('-'), None)
        self.assertEqual(encodes(None), '-')
        self.assertEqual(encodes(True), 'b\x01')
        self.assertEqual(encodes(False), 'b\x00')
        self.assertEqual(decodes('b\x01'), True)
        self.assertEqual(decodes('b\x00'), False)
        self.assertEqual(decodes('i\x00\x00\x00\x2A'), 42)
        self.assertEqual(encodes(42), 'i\x00\x00\x00\x2A')
        big_e = encodes(3000000000)
        self.assertEqual(big_e[0], 'q')
        self.assertEqual(decodes(big_e), 3000000000)
        self.assertEqual(encodes(0x85, encoder=BYTE), 'B\x85')
        self.assertEqual(decodes('B\x85'), 0x85)
        self.assertEqual(encodes(0x7654, encoder=INT16), 'h\x76\x54')
        self.assertEqual(decodes('h\x76\x54'), 0x7654)
        f_42_e = encodes(42.0)
        self.assertEqual(decodes(f_42_e), 42.0)

        # Ascii str encodes as ascii 0x0A
        self.assertEqual(encodes('Fred'), 'a\x00\x00\x00\x04Fred')
        self.assertEqual(decodes('a\x00\x00\x00\x04Fred'), 'Fred')
        self.assertEqual(encodes('\x81\x82'), 'r\x00\x00\x00\x02\x81\x82')
        self.assertEqual(decodes('r\x00\x00\x00\x02\x81\x82'), '\x81\x82')
        self.assertEqual(encodes(u'Fred'), 'u\x00\x00\x00\x04Fred')
        self.assertEqual(decodes('u\x00\x00\x00\x04Fred'), u'Fred')
        self.assertEqual(type(decodes('u\x00\x00\x00\x04Fred')), unicode)
        self.assertEqual(encodes('Fred', encoder=TOKEN), 'k\x00\x04Fred')
        self.assertEqual(decodes('k\x00\x04Fred'), 'Fred')

        t = datetime.datetime(1965,07,18,15,45) # 3:45pm 18/7/1965.
        self.assertEqual(decodes(encodes(t)), t)

        l_42_e = 'LA\x00\x00\x00\x01i\x00\x00\x00*'
        self.assertEqual(encodes([42]), l_42_e)
        self.assertEqual(decodes(l_42_e), [42])
        m1_1_e = 'Li\x00\x00\x00\x02\xff\xff\xff\xff\x00\x00\x00\x01'
        self.assertEqual(encodes([-1,1], encoder=ARRAY(INT32)), m1_1_e)
        self.assertEqual(decodes(m1_1_e), [-1, 1])
        tup_e = 'T\x00\x00\x00\x02iA\x00\x00\x00*-'
        e = TUPLE(INT32, ANY)
        self.assertEqual(encodes([42, None], encoder=e), tup_e)
        self.assertEqual(decodes(tup_e), [42, None])
        e = VECTOR(BYTE, 3)
        vec_3 = 'VB\x00\x00\x00\x03\x03\x06\x09'
        self.assertEqual(encodes([3, 6, 9], encoder=e), vec_3)
        self.assertEqual(decodes(vec_3), [3, 6, 9])

        tom_5_e = 'MkA\x00\x00\x00\x01\x00\x03tomi\x00\x00\x00\x05'
        self.assertEqual(encodes({'tom':5}), tom_5_e)
        self.assertEqual(decodes(tom_5_e), {'tom':5})

    def testCtx(self):
        REG.register('custom', 4, ANY)
        REG.addCustom('custom', Custom.construct)

        enc = encodes(Custom(-1,0), ctx=REG)
        self.assertEqual(decodes(enc, ctx=REG), Custom(-1,0))

        # If we don't have the custom decoder, it safely decodes to a record
        # which can be re-encoded without loss of information.
        rec = decodes(enc)
        self.assertEqual(type(rec), Record)
        self.assertEqual(encodes(rec), enc)

        # We can nest and embed in POD structures.
        fancy = [Custom(0,1), Custom(Custom('x','y'), True)]
        f_enc = encodes(fancy, ctx=REG)
        self.assertEqual(decodes(f_enc, ctx=REG), fancy)


    def testStruct(self):
        s = STRUCT([('name', TEXT), ('dob', TIME)])
        dob = datetime.datetime(1973,4,22)
        val = {'name': u'Fred', 'dob': dob}
        enc = encodes(val, encoder=s)
        self.assertEqual(decodes(enc), val)

        REG.register('person', 1, s)
        msg = Record('person', val)
        m_enc = encodes(msg, ctx=REG)
        self.assertEqual(decodes(m_enc, ctx=REG), msg)

        # By adding a CONST field we can decode the same data with a new field.
        s1 = STRUCT([('name', TEXT), ('dob', TIME), ('level', CONST(42))])
        REG.register('person', 1, s1)
        val1 = {'name': u'Fred', 'dob': dob, 'level': 42}
        msg1 = decodes(m_enc, ctx=REG)
        self.assertEqual(msg1.value, val1)

        # Encoding with the CONST field still produces the same value.
        m_enc1 = encodes(msg1, ctx=REG)
        self.assertEqual(m_enc1, m_enc)

        # We want to encode a real level for all new records.
        s2 = STRUCT([('name', TEXT), ('dob', TIME), ('level', INT16)])
        REG.register('person', 2, s2)

        # When messages are encoded the codec is found up by name.
        # The most recently registered codec with a given name will be used.
        # Therefore when we encode msg now, the level will be encoded as well.
        msg1.value['level'] = 9
        m_enc2 = encodes(msg1, ctx=REG)
        msg2 = decodes(m_enc2, ctx=REG)
        self.assertEqual(msg2.value['level'], 9)

        # When decoding, the codec is found by id. The registry still
        # has s1 registered for id 1, so records encoded with s or s1
        # can still be decoded.
        msg3 = decodes(m_enc, ctx=REG)
        self.assertEqual(msg3.value, val1)

    def testEnum(self):
        GBE = ENUM({'GOOD':0, 'BAD':1, 'UGLY':2})
        s = STRUCT([('name', TEXT), ('mood', GBE)])
        REG.register('state', 3, s)

        msg = Record('state', {'name':u'Barney', 'mood':'UGLY'})
        enc = encodes(msg, ctx=REG)
        msg1 = decodes(enc, ctx=REG)
        self.assertEqual(msg1.value['mood'], 'UGLY')

if __name__ == '__main__':
    unittest.main()
