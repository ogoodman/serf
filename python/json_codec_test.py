#!/usr/bin/python

"""Tests for JSON_CODEC and JSONCodecCtx."""

import unittest
from json_codec import JSON_CODEC
from rpc_handler import JSONCodecCtx

class FakeRPC(object):
    node_id = 'node'

class KeyValue(object):
    serialize = ('key', 'value', 'skey')

    def __init__(self, key, value, skey=None):
        self.key = key
        self.value = value
        self.skey = skey

HOOKS = {
    'KeyValue': lambda _, args: KeyValue(*args)
}

CTX = JSONCodecCtx(FakeRPC(), hooks=HOOKS)

class JSONCodecTest(unittest.TestCase):
    def test(self):
        kv = KeyValue(44, 'fred')
        enc = JSON_CODEC.encode(kv, CTX)

        dec = JSON_CODEC.decode(enc, CTX)
        self.assertEqual(dec.key, 44)
        self.assertEqual(dec.value, 'fred')

if __name__ == '__main__':
    unittest.main()
