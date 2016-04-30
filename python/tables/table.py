"""An in memory Table."""

import re
import copy
import sys

from serf.publisher import Publisher
from serf.serializer import decodes, encodes

from query import getMember, setMember, checkField, matchQuery
from merge_records import mergeRecords

class TableCodec(object):
    def encodes(self, obj):
        return encodes(obj)

    def decodes(self, data):
        return decodes(data)

class FieldValue(object):
    serialize = ('field', 'value', 'when')

    def __init__(self, field, value, when=None):
        checkField(field)
        if field == '':
            raise ValueError('Field cannot be empty in FieldValue')

        self.field = field
        self.value = value
        self.when = when

    def update(self, rec, vrec):
        if self.when is not None and not matchQuery(self.when, rec):
            return False
        return setMember(rec, self.field, self.value)

class CopyField(object):
    serialize = ('field', 'copy', 'when')

    def __init__(self, field, copy, when=None):
        checkField(field)
        if field == '':
            raise ValueError('Field cannot be empty in CopyField')

        self.field = field
        self.copy = copy
        self.when = when

    def update(self, rec, vrec):
        if vrec is None:
            return False
        return setMember(rec, self.field, getMember(vrec, self.copy))

def updateFields(rec, fields, vrec=None):
    """Updates values in rec.

    :param rec: POD object to update
    :param fields: list of field updaters (e.g. FieldValue, CopyField)
    :param vrec: POD object which may supply values
    """
    modified = False
    for f in fields:
        if f.update(rec, vrec):
            modified = True
    return modified

class KeyValuePair(object):
    serialize = ('key', 'value')

    def __init__(self, key, value):
        self.key = key
        self.value = value

class SKeyKeyValueTriple(object):
    serialize = ('key', 'value', 'skey')

    def __init__(self, key, value, skey):
        self.key = key
        self.value = value
        self.skey = skey

class KeyValueChange(object):
    serialize = ('key', 'value', 'old')

    def __init__(self, key, value, old):
        self.key = key
        self.value = value
        self.old = old

class JoinSpec(object):
    serialize = ('leftCol', 'rightCol', 'type', 'limit', 'nulls', 'keepOpen')

    def __init__(self, leftCol, rightCol, type, limit=0, nulls=False, keepOpen=False):
        self.leftCol = leftCol
        self.rightCol = rightCol
        self.type = type
        self.limit = limit
        self.nulls = nulls
        self.keepOpen = keepOpen

def getIndexer(spec):
    if spec.startswith('cols:'):
        return ColsIndexer(spec[5:])
    return Indexer(spec)

def normalizeSpec(spec):
    return spec[:-4] + 'int 8' if spec.endswith(' time') else spec

class Indexer(object):
    def __init__(self, spec):
        bits = spec.split()
        if len(bits) < 2:
            raise Exception('Indexer must have a type')
        self.col = bits[0]
        checkField(self.col)
        self.type = bits[1]
        if self.type not in ['int', 'str', 'data', 'str-i', 'data-i', 'numeric']:
            raise Exception('Unsupported type: %r' % self.type)
        self.fold_case = self.type.endswith('-i')

    def __call__(self, rec):
        field = getMember(decodes(rec), self.col)
        if self.type == 'int':
            if type(field) not in (int, long):
                return None
        else:
            if type(field) not in (str, unicode):
                return None
        return field.lower() if self.fold_case else field

    def normalize(self, key):
        if self.fold_case and type(key) in (str, unicode):
            key = key.lower()
        return key


class ColsIndexer(object):
    def __init__(self, spec):
        self.indexers = map(Indexer, spec.split(','))
        self.template = '::'.join(['%s'] * len(self.indexers))

    def __call__(self, raw_rec):
        try:
            rec = decodes(raw_rec)
        except:
            return '\0'
        values = [i._getSKey(rec) for i in self.indexers]
        return self.template % tuple(values)

    def normalize(self, key):
        split_key = key.split('::')
        if len(split_key) != len(self.indexers):
            return key
        split_nkey = [i.normalize(k) for i, k in zip(self.indexers, split_key)]
        return '::'.join(split_nkey)

class Table(Publisher):
    def __init__(self, client, id, indexers=None):
        Publisher.__init__(self)
        self.client = client
        self.id = id
        self.primary = {}
        self.indexers = indexers or {}
        self.indices = {}
        self.pkey = 0
        for col in self.indexers:
            self.indices[col] = {}
        self.sink = None
        self.time_index = None

    def setBatch(self, records): 
        for r in records:
            self.set(r.key, r.value, notify=False)

    def pkeys(self):
        return list(sorted(self.primary.keys()))
    
    def countQuery(self, query):
        return len(self._selectQuery(query))

    def _maxIndex(self):
        return max(self.primary.keys())

    def _index(self, pkey, data):
        for col, indexer in self.indexers.iteritems():
            key = indexer(data)
            index = self.indices[col]
            if key not in index:
                index[key] = []
            if pkey not in index[key]:
                index[key].append(pkey)

    def _unindex(self, pkey, data):
        for col, indexer in self.indexers.iteritems():
            key = indexer(data)
            index = self.indices[col]
            if key in index and pkey in index[key]:
                index[key].remove(pkey)
                if len(index[key]) == 0:
                    del index[key]
                    
    def copy(self, id):
        t = self._copy()
        t.id = id
        self.client.grid.TABLES[id] = t

    def erase(self):
        self.client.eraseDb(self.id)
        # The MockClient currently abuses a ClientProxy in openDb
        # in order to make iter methods realistic. It puts a reference
        # to the table in, rather than a proxy and opener.
        # Because the ClientProxy hangs onto this Table, we need
        # to simulate the erase by clearing the table as well.
        self.primary = {}
        self.pkey = 0
        self.indexers = {}
        self.indices = {}
        
    def _copy(self):
        from copy import deepcopy
        copy = Table(self.client, self.id)
        copy.primary = deepcopy(self.primary)
        copy.indexers = deepcopy(self.indexers)
        copy.indices = deepcopy(self.indices)
        copy.pkey = self.pkey
        return copy

    def _ensureIndex(self, unspec):
        spec = normalizeSpec(unspec)
        if spec not in self.indexers:
            self.indexers[spec] = indexer = getIndexer(spec)
            self.indices[spec] = index = {}
            for pkey, data in self.primary.iteritems():
                key = indexer(data)
                if key not in index:
                    index[key] = []
                if pkey not in index[key]:
                    index[key].append(pkey)

    def _getIndexer(self, unspec):
        spec = normalizeSpec(unspec)
        self._ensureIndex(spec)
        if spec not in self.indexers:
            self.indexers[spec] = getIndexer(spec)
        return self.indexers[spec]

    def _getIndex(self, spec):
        return self.indices[normalizeSpec(spec)]

    def size(self):
        return len(self.primary)

    def _put(self, data, notify=True):
        self.pkey += 4
        self.primary[self.pkey] = data
        if notify:
            info = KeyValueChange(self.pkey, data, '')
            self.notify('change', info)
            self.notify('key:%s' % self.pkey, info)
        self._index(self.pkey, data)
        
    def insert(self, data):
        self._put(data)
        return self.pkey
    
    def insertBatch(self, records):
        for r in records:
            self._put(r, notify=False)
            
    def set(self, pkey, data, notify=True):
        try:
            old = self.primary[pkey]
        except KeyError:
            old = ''
        else:
            self._unindex(pkey, old)
        self.primary[pkey] = data
        if notify:
            info = KeyValueChange(pkey, data, old)
            self.notify('change', info)
            self.notify('key:%s' % pkey, info)
        self._index(pkey, data)
        if pkey > self.pkey:
            self.pkey = pkey

    def _update(self, pkey, values, vrec):
        rec = decodes(self.select(pkey))
        modified = updateFields(rec, values, vrec)
        if modified:
            self.set(pkey, encodes(rec))

    def update(self, pkey, values, vrec=None):
        if vrec is not None:
            vrec = decodes(vrec)
        self._update(pkey, values, vrec)

    def updateKey(self, spec, key, values):
        matches = self.selectKey(spec, key)
        pkeys = []
        for kv in matches:
            rec = decodes(kv.value)
            if updateFields(rec, values):
                pkeys.append(kv.key)
                self.set(kv.key, encodes(rec))
        return pkeys

    def updateQuery(self, query, values):
        matches = self._selectQuery(query)
        count = 0
        for kv in matches:
            rec = decodes(kv.value)
            if updateFields(rec, values):
                count += 1
                self.set(kv.key, encodes(rec))
        return count

    def countKey(self, spec, value):
        return len(self.selectKey(spec, value))

    def pop(self, pkey, notify=True):
        try:
            data = self.primary[pkey]
        except KeyError:
            raise KeyError(pkey)
        self._unindex(pkey, data)

        del self.primary[pkey]
        if notify:
            info = KeyValueChange(pkey, '', data)
            self.notify('delete', info)
            self.notify('key:%s' % pkey, info)
        return data

    def remove(self, pkey):
        if pkey not in self.primary:
            return
        self.pop(pkey)

    def removeAll(self):
        count = len(self.primary)
        info = KeyValueChange(-1, '', '')
        for pkey in list(self.primary):
            self.pop(pkey, notify=False)
            self.notify('key:%s' % pkey, info)
        if count > 0:
            self.notify('delete', KeyValueChange(-count, '', ''))
        self.pkey = 0
        return count

    def select(self, pkey):
        if int(pkey) not in self.primary:
            raise KeyError(pkey)
        return self.primary[pkey]

    def selectAll(self):
        return [KeyValuePair(pkey, data)
                for pkey, data in sorted(self.primary.iteritems())]

    def values(self):
        return [data for pkey, data in sorted(self.primary.items())]

    def selectPKR(self, lo, hi):
        return [KeyValuePair(pkey, data)
                for pkey, data in sorted(self.primary.items())
                if lo <= pkey < hi]

    def selectKey(self, spec, key, query=None):
        if spec.startswith('# int'):
            results = []
            try:
                value = self.primary[key]
                results.append(KeyValuePair(key, value))
            except KeyError:
                pass
        else:
            key = self._getIndexer(spec).normalize(key)
            index = self._getIndex(spec)
            if key not in index:
                return []
            results = [KeyValuePair(pkey, self.primary[pkey])
                       for pkey in sorted(index[key])]
        if query is None:
            return results
        return [kv for kv in results if matchQuery(query, kv.value)]

    def selectUniqueKey(self, spec, key):
        key = self._getIndexer(spec).normalize(key)
        index = self._getIndex(spec)
        pkeys = [pk[0] for sk, pk in sorted(index.iteritems())
                 if sk.startswith(key)]
        return [KeyValuePair(pkey, self.primary[pkey]) for pkey in pkeys]

    def countUniqueKey(self, spec, key):
        return len(self.selectUniqueKey(spec, key))

    def selectUniqueKeyRange(self, spec, key, lo, hi):
        return self.selectUniqueKey(spec, key)[lo:hi]

    def selectKeyRange(self, spec, key, lo, hi, query=None):
        return self.selectKey(spec, key, query)[lo:hi]

    def setKey(self, spec, message, replace=True):
        """Inserts or updates a record indexed by spec.

        If replace is False and a matching record already
        exists, the update is rejected and a key of -1 is returned.
        """
        indexer = self._getIndexer(spec)
        key = indexer(message)
        to_remove = [item.key for item in self.selectKey(spec, key)]
        if len(to_remove) > 0:
            if not replace:
                return -1
            for pkey in to_remove[1:]:
                self.remove(pkey)
            self.set(to_remove[0], message)
            return to_remove[0]
        else:
            return self.insert(message)

    def _selectQuery(self, query):
        return [r for r in self.selectAll() if matchQuery(query, r.value)]

    def selectQuery(self, query, lo=0, hi=None):
        return self._selectQuery(query)[lo:hi]

    def selectQueryPKR(self, q, lo, hi):
        return [kv for kv in self._selectQuery(q) if lo <= kv.key < hi]

    def selectText(self, text):
        if type(text) is unicode:
            text = text.encode('utf8')
        ltext = text.lower()
        return [kv for kv in self.selectAll() if ltext in kv.value.lower()]

    def firstByKey(self, spec):
        self._ensureIndex(spec)
        index = self._getIndex(spec)
        if len(index) == 0:
            raise Exception('empty')
        skey = sorted(index.keys())[0]
        pkey = index[skey][0]
        return SKeyKeyValueTriple(pkey, self.primary[pkey], skey)

    def removeKey(self, spec, key):
        to_remove = [item.key for item in self.selectKey(spec, key)]
        for pkey in to_remove:
            self.remove(pkey)
        return len(to_remove)

    def removeQuery(self, query):
        to_remove = [
            item.key for item in self._selectQuery(query)]
        for pkey in to_remove:
              self.remove(pkey)
        return len(to_remove)

    def selectRange(self, begin, end):
        return [KeyValuePair(i, self.primary[i])
                for i in sorted(self.primary.keys())[begin:end]]
        
    def selectSortedRange(self, query, index, begin, end, desc):
        assert False, 'not implemented'

    def matchKeyQuery(self, pkey, q):
        return matchQuery(q, self.select(pkey))

    def _join(self, left, join, query, func):
        for lkv in left:
            self._join1(lkv, join, query, func)

    def _join1(self, lkv, join, query, func):
        l_col, r_col, type = join.leftCol, join.rightCol, join.type
        if r_col != '#':
            r_col = ':' + r_col
        spec = '%s %s' % (r_col, type)
        limit = join.limit or sys.maxint
        l_pk = lkv.key
        left = decodes(lkv.value)
        try:
            key = l_pk if l_col == '#' else left[l_col]
        except (KeyError, AttributeError):
            to_join = []
        else:
            to_join = self.selectKeyRange(spec, key, 0, limit, query)
        if not to_join and join.nulls:
            to_join.append(KeyValuePair(0, encodes({})))
        for kv in to_join:
            right = decodes(kv.value)
            func(l_pk, left, kv.key, right)

    def join(self, left, join, query, merge):
        results = []
        def buildJoin(s_pk, s_rec, r_pk, r_rec):
            out = mergeRecords(s_pk, s_rec, r_pk, r_rec, merge, {})
            results.append(KeyValuePair(s_pk, encodes(out)))
        self._join(left, join, query, buildJoin)
        return results

    def updateIter(self, stream, join, query, values):
        count = [0]
        join.nulls = 0 # don't want any cases of r_pk not in the table.
        def doUpdate(s_pk, s_rec, r_pk, r_rec):
            self._update(r_pk, values, s_rec)
            count[0] += 1
        self._join(stream, join, query, doUpdate)
        return count[0]

    def setTimeIndex(self, index):
        self.time_index = index

    def getTimeIndex(self):
        return self.time_index

    def setSink(self, sink):
        self.sink = sink

    def getSink(self):
        return self.sink

    def maxId(self):
        return max(list(self.primary))

class Client(object):
    def openDb(self, name):
        return Table(self, name)

    def eraseDb(self, name):
        #try:
        #    del self.grid.TABLES[name]
        #except KeyError:
        #    pass
        pass
