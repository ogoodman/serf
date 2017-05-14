"""Client handle for Tables.

Handles encoding and decoding of table records.
"""

from table import TableCodec
from serf.weak_list import getAdapter

class TableHandle(object):
    serialize = ('_table',)

    def __init__(self, table):
        self._table = table
        self._codec = TableCodec()

    def _decode_kvs(self, kvs):
        return [(kv.key, kv.value) for kv in kvs]

    def _encode_kvs(self, items):
        return [KeyValue(k, v) for k, v in items]

    def _do_notify(self, cb, event, kvc):
        cb(event, [kvc.key, kvc.old, kvc.value])

    def subscribe(self, event, cb):
        self._table.subscribe(event, getAdapter(cb, self._do_notify))

    def unsubscribe(self, event, cb):
        self._table.unsubscribe(event, getAdapter(cb, self._do_notify))

    # query

    def get(self, key):
        return self._table.get(key)

    def pkeys(self, filter=None):
        return self._table.pkeys(filter)

    def count(self, filter=None):
        return self._table.count(filter)

    def select(self, filter=None):
        return self._decode_kvs(self._table.select(filter))

    def values(self, filter=None):
        return self._table.values(filter)

    def join(self, left, join, query, merge):
        kvs = self._table.join(self._encode_kvs(left), join, query, merge)
        return self._decode_kvs(kvs)

    def maxPK(self):
        return self._table.maxPK()

    # modify

    def set(self, key, value, notify=True):
        self._table.set(key, value, notify)

    def setKey(self, index, value, replace=True):
        self._table.setKey(index, value, replace)

    def setBatch(self, items, notify=True):
        self._table.setBatch(self._encode_kvs(items), notify)

    def insert(self, values, notify=True):
        if type(values) is not list:
            values = [values]
        return self._table.insert(values, notify)

    def update(self, filter, values, model=None):
        self._table.update(filter, values, model)

    def updateIter(self, items, join, query, values):
        return self._table.updateIter(self._encode_kvs(items), join, query, values)

    def pop(self, filter=None, notify=True):
        return self._decode_kvs(self._table.pop(filter))

    def remove(self, filter=None):
        return self._table.remove(filter)

