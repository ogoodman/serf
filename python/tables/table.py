"""An in memory Table."""

import re
import copy
import sys
from itertools import islice

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

class KeyValue(object):
    serialize = ('key', 'value', 'skey')

    def __init__(self, key, value, skey=None):
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

# generators

class All(object):
    serialize = ()

    def generate(self, table):
        return table._selectAll()

class PKey(object):
    serialize = ('pk', 'required')

    def __init__(self, pk, required=True):
        self.pk = pk
        self.required = required

    def generate(self, table):
        return table._get(self.pk, self.required)

class Key(object):
    serialize = ('index', 'key')

    def __init__(self, index, key):
        self.index = index
        self.key = key

    def generate(self, table):
        return table._selectKey(self.index, self.key)

class KeyPrefix(object):
    serialize = ('index', 'prefix', 'unique')

    def __init__(self, index, prefix, unique=False):
        self.index = index
        self.prefix = prefix
        self.unique = unique

    def generate(self, table):
        return table._selectKeyPrefix(self.index, self.prefix, self.unique)

class KeyRange(object):
    serialize = ('index', 'lo', 'hi', 'reverse')

    def __init__(self, index, lo=None, hi=None, reverse=False):
        self.index = index
        self.lo = lo
        self.hi = hi
        self.reverse = reverse

    def generate(self, table):
        return table._selectKeyRange(self.index, self.lo, self.hi, self.reverse)

# filters

class Range(object):
    serialize = ('begin', 'end')

    def __init__(self, begin, end=None):
        self.begin = begin
        self.end = end

    def filter(self, iter):
        return islice(iter, self.begin, self.end)

class Query(object):
    serialize = ('query',)

    def __init__(self, query):
        self.query = query

    def filter(self, iter):
        for kv in iter:
            if matchQuery(self.query, kv.value):
                yield kv

class Text(object):
    serialize = ('text',)

    def __init__(self, text):
        if type(text) is unicode:
            text = text.encode('utf8')
        self.text = text

    def filter(self, iter):
        for kv in iter:
            if self.text in kv.value:
                yield kv

class PKeyRange(object):
    serialize = ('lo', 'hi')

    def __init__(self, lo, hi):
        self.lo = lo
        self.hi = hi

    def generate(self, table):
        return table._selectPKR(self.lo, self.hi)

    def filter(self, iter):
        for kv in iter:
            if self.lo <= kv.key < self.hi:
                yield kv

def genFilters(filter):
    if filter is None:
        return All(), []
    if type(filter) is not list:
        filter = [filter]
    if not filter:
        return All(), filter
    if hasattr(filter[0], 'generate'):
        return filter[0], filter[1:]
    return All(), filter

class Table(Publisher):
    serialize = ('primary', 'indices', 'pkey')

    def __init__(self, primary=None, indices=None, pkey=None):
        Publisher.__init__(self)
        self.primary = primary or {}
        self.indices = indices or {}
        self.pkey = pkey or 0
        self._indexers = {}

    def select(self, filter=None):
        gen, filters = genFilters(filter)
        result = gen.generate(self)
        for f in filters:
            if not hasattr(f, 'filter'):
                f = Query(f) # assume it's a query
            result = f.filter(result)
        # Should we return an interator?
        return list(result)

    def _selectAll(self):
        return [KeyValue(pkey, data)
                for pkey, data in sorted(self.primary.iteritems())]

    def _selectPKR(self, lo, hi):
        return [KeyValue(pkey, data)
                for pkey, data in sorted(self.primary.items())
                if lo <= pkey < hi]

    def _selectKey(self, spec, key, unique=False):
        if spec.startswith('# int'):
            results = []
            try:
                value = self.primary[key]
                results.append(KeyValue(key, value, key))
            except KeyError:
                pass
        else:
            key = self._getIndexer(spec).normalize(key)
            index = self._getIndex(spec)
            if key not in index:
                return []
            results = [KeyValue(pkey, self.primary[pkey], key)
                       for pkey in sorted(index[key])]
        return results

    def _selectKeyPrefix(self, spec, prefix, unique=False):
        prefix = self._getIndexer(spec).normalize(prefix)
        index = self._getIndex(spec)
        pkl = [pk for sk, pk in sorted(index.iteritems()) if sk.startswith(prefix)]
        if unique:
            pkeys = [pk[0] for pk in pkl]
        else:
            pkeys = []
            for pk in pkl: pkeys.extend(pk)
        return [KeyValue(pkey, self.primary[pkey]) for pkey in pkeys]

    def _selectKeyRange(self, spec, lo=None, hi=None, reverse=False):
        normalize = self._getIndexer(spec).normalize
        index = self._getIndex(spec)
        range = sorted(index.iteritems(), reverse=reverse)
        if lo is not None:
            lo = normalize(lo)
            range = dropwhile(lambda kv: kv[0] < lo, range)
        if hi is not None:
            hi = normalize(hi)
            range = takewhile(lambda kv: kv[0] < hi, range)
        for sk, pks in range:
            for pk in pks:
                yield KeyValue(pk, self.primary[pk], sk)

    def count(self, filter=None):
        if filter is None:
            return len(self.primary)
        gen, filters = genFilters(filter)
        return len(self.select(filter))

    def setBatch(self, records, notify=True): 
        for r in records:
            self.set(r.key, r.value, notify)

    def pkeys(self, filter=None):
        return [kv.key for kv in self.select(filter)]
    
    def _index(self, pkey, data):
        for col, index in self.indices.iteritems():
            key = self._getIndexer(col)(data)
            if key is None:
                continue
            if key not in index:
                index[key] = []
            if pkey not in index[key]:
                index[key].append(pkey)

    def _unindex(self, pkey, data):
        for col, index in self.indices.iteritems():
            key = self._getIndexer(col)(data)
            if key in index and pkey in index[key]:
                index[key].remove(pkey)
                if len(index[key]) == 0:
                    del index[key]
                    
    def _erase(self):
        self.primary = {}
        self.indices = {}
        self.pkey = 0
        self._indexers = {}
        
    def _ensureIndex(self, unspec):
        spec = normalizeSpec(unspec)
        if spec not in self.indices:
            self.indices[spec] = index = {}
            indexer = self._getIndexer(spec)
            for pkey, data in self.primary.iteritems():
                key = indexer(data)
                if key is None:
                    continue
                if key not in index:
                    index[key] = []
                if pkey not in index[key]:
                    index[key].append(pkey)

    def _getIndexer(self, unspec):
        spec = normalizeSpec(unspec)
        self._ensureIndex(spec)
        if spec not in self._indexers:
            self._indexers[spec] = getIndexer(spec)
        return self._indexers[spec]

    def _getIndex(self, spec):
        return self.indices[normalizeSpec(spec)]

    def _put(self, data, notify=True):
        self.pkey += 4
        self.primary[self.pkey] = data
        self._index(self.pkey, data)
        if notify:
            info = KeyValueChange(self.pkey, data, '')
            self.notify('change', info)
            self.notify('key:%s' % self.pkey, info)
        
    def insert(self, records, notify=True):
        keys = []
        for r in records:
            self._put(r, notify)
            keys.append(self.pkey)
        return keys
            
    def set(self, pkey, data, notify=True):
        try:
            old = self.primary[pkey]
        except KeyError:
            old = ''
        else:
            self._unindex(pkey, old)
        self.primary[pkey] = data
        self._index(pkey, data)
        if pkey > self.pkey:
            self.pkey = pkey
        if notify:
            info = KeyValueChange(pkey, data, old)
            self.notify('change', info)
            self.notify('key:%s' % pkey, info)

    def _update(self, pkey, values, vrec):
        rec = decodes(self.get(pkey))
        if updateFields(rec, values, vrec):
            self.set(pkey, encodes(rec))

    def update(self, filter, values, model=None):
        pkeys = []
        if model is not None:
            model = decodes(model)
        for kv in self.select(filter):
            rec = decodes(kv.value)
            if updateFields(rec, values, model):
                pkeys.append(kv.key)
                self.set(kv.key, encodes(rec))
        return pkeys

    def _pop(self, pkey, notify=True):
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

    def pop(self, filter=None, notify=True):
        kvs = self.select(filter)
        for kv in kvs:
            self._pop(kv.key, notify)
        return kvs

    def _removeAll(self):
        count = len(self.primary)
        info = KeyValueChange(-1, '', '')
        for pkey in list(self.primary):
            self._pop(pkey, notify=False)
            self.notify('key:%s' % pkey, info)
        if count > 0:
            self.notify('delete', KeyValueChange(-count, '', ''))
        self.pkey = 0
        return count

    def remove(self, filter=None):
        if filter is None:
            return self._removeAll()
        to_remove = [item.key for item in self.select(filter)]
        for pkey in to_remove:
            self._pop(pkey)
        return len(to_remove)

    def _get(self, pkey, required):
        value = self.primary.get(pkey)
        if required and value is None:
            raise KeyError(pkey)
        return [] if value is None else [KeyValue(pkey, value)]

    def get(self, pkey):
        if int(pkey) not in self.primary:
            raise KeyError(pkey)
        return self.primary[pkey]

    def values(self, filter=None):
        return [pk.value for pk in self.select(filter)]

    def setKey(self, spec, message, replace=True):
        """Inserts or updates a record indexed by spec.

        If replace is False and a matching record already
        exists, the update is rejected and a key of -1 is returned.
        """
        indexer = self._getIndexer(spec)
        key = indexer(message)
        to_remove = [item.key for item in self._selectKey(spec, key)]
        if len(to_remove) > 0:
            if not replace:
                return -1
            for pkey in to_remove[1:]:
                self._pop(pkey)
            self.set(to_remove[0], message)
            return to_remove[0]
        else:
            return self.insert([message])[0]

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
            filters = [query, Range(0, limit)] if query is not None else [Range(0, limit)]
            to_join = self.select([Key(spec, key)] + filters)
        if not to_join and join.nulls:
            to_join.append(KeyValue(0, encodes({})))
        for kv in to_join:
            right = decodes(kv.value)
            func(l_pk, left, kv.key, right)

    def join(self, left, join, query, merge):
        results = []
        def buildJoin(s_pk, s_rec, r_pk, r_rec):
            out = mergeRecords(s_pk, s_rec, r_pk, r_rec, merge, {})
            results.append(KeyValue(s_pk, encodes(out)))
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

    def maxPK(self):
        return max(self.primary)

    def _on_addref(self):
        self.subscribe('change', self.ref._save)
        self.subscribe('delete', self.ref._save)

class Client(object):
    def __init__(self):
        self._tables = {}

    def openDb(self, name):
        if name not in self._tables:
            self._tables[name] = Table()
        return self._tables[name]

    def eraseDb(self, name):
        table = self._tables.pop(name, None)
        if table is not None:
            table._erase()
