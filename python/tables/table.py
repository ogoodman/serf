"""An in memory Table."""

import re
import copy
import sys
from itertools import islice

from serf.publisher import Publisher
from serf.serializer import decodes, encodes

from query import getMember, setMember, checkField, QTerm

#def encodes(r):
#    return dict(r)
#def decodes(r):
#    return dict(r)

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
        if self.when is not None and not self.when.match(rec):
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

    def __repr__(self):
        return repr((self.key, self.value, self.skey))

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

class MergeTerm(object):
    serialize = ('source', 'fieldIn', 'fieldOut')

    def __init__(self, source, fieldIn, fieldOut):
        self.source = source
        self.fieldIn = fieldIn
        self.fieldOut = fieldOut

def setField(i_pk, i_rec, f, o_f, o_rec, o_done):
    # FIXME: use getMember/setMember rather than [].
    if o_f not in o_done:
        try:
            o_rec[o_f] = (i_pk if f == '#' else i_rec[f])
        except KeyError:
            pass
        o_done.add(o_f)

def mergeRecords(l_pk, l_rec, r_pk, r_rec, spec, o_rec):
    l_done = set()
    r_done = set()
    o_done = set()
    for term in spec:
        lr, f_in, f_out = term.source, term.fieldIn, term.fieldOut
        if term.source not in 'LR':
            print 'bad spec term MergeTerm%r' % ((lr, f_in, f_out),)
            continue
        i_pk, i_rec, i_done = (
            (l_pk, l_rec, l_done) if lr == 'L' else (r_pk, r_rec, r_done))

        if f_in == '*':
            if '%' not in f_out:
                print 'bad spec term MergeTerm%r' % ((lr, f_in, f_out),)
                continue
            for f in i_rec.keys():
                if f in i_done:
                    continue
                i_done.add(f)
                o_f = f_out.replace('%', f)
                setField(i_pk, i_rec, f, o_f, o_rec, o_done)
        else:
            if f_in in i_done:
                continue
            i_done.add(f_in)
            if f_out == '.':
                continue
            setField(i_pk, i_rec, f_in, f_out, o_rec, o_done)
    return o_rec

def makeTerm(text):
    """Converts a merge term string to a MergeTerm

    A merge term takes the form 
        <source>:<field-in>[-><field-out>]
    where <source> is 'L' or 'R', <field-in> specifies which
    field(s) to read from the source record, and <field-out> specifies
    which field(s) to write to the output record.

    NOTE: L is the stream, R is the table.
 
    The source field, <field-in> may be
        the name of a field,
        '*' meaning all fields, or
        '#' meaning the primary key of the source record.
    The output field may be
        the name of a field,
        when the source is *, a template containing a % which is substituted,
        '.' meaning the value is to be discarded.
    If no output field is specified, the output field defaults to
        the input field name when it is not special, or
        '%' when the input field is '*'.
    """
    source, field_in = text.split(':', 1)
    if source not in 'LR':
        raise Exception('Bad merge term:%r' % text)
    field_bits = field_in.split('->', 1)
    if len(field_bits) == 2:
        field_in, field_out = field_bits
    else:
        if field_in == '*':
            field_out = '%'
        elif field_in == '#':
            raise Exception('Bad merge term:%r' % text)
        else:
            field_out = field_in
    return MergeTerm(source, field_in, field_out)

def mergeSpec(text):
    return map(makeTerm, text.split())
    
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

    def index_r(self, rec):
        return self.index(decodes(rec))

    def index(self, rec):
        field = getMember(rec, self.col)
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

    def index_r(self, raw_rec):
        try:
            return self.index(decodes(raw_rec))
        except:
            return '\0'

    def index(self, rec):
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
            try:
                rec = decodes(kv.value)
            except:
                # Ignore/reject records which cannot be decoded.
                continue
            if self.query.match(rec):
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
    serialize = ('_primary', '_indices', '_pkey', '_subs')

    def __init__(self, primary=None, indices=None, pkey=None, subs=None):
        Publisher.__init__(self, subs)
        self._primary = primary or {}
        self._indices = indices or {}
        self._pkey = pkey or 0
        self._indexers = {}

    def select_r(self, filter=None):
        gen, filters = genFilters(filter)
        result = gen.generate(self)
        for f in filters:
            if not hasattr(f, 'filter'):
                f = Query(f) # assume it's a query
            result = f.filter(result)
        # Should we return an iterator?
        return list(result)

    def select(self, filter=None):
        kvl = self.select_r(filter)
        for kv in kvl:
            kv.value = decodes(kv.value)
        return kvl

    def _selectAll(self):
        return [KeyValue(pkey, data)
                for pkey, data in sorted(self._primary.iteritems())]

    def _selectPKR(self, lo, hi):
        return [KeyValue(pkey, data)
                for pkey, data in sorted(self._primary.items())
                if lo <= pkey < hi]

    def _selectKey(self, spec, key, unique=False):
        if spec.startswith('# int'):
            results = []
            try:
                value = self._primary[key]
                results.append(KeyValue(key, value, key))
            except KeyError:
                pass
        else:
            key = self._getIndexer(spec).normalize(key)
            index = self._getIndex(spec)
            if key not in index:
                return []
            results = [KeyValue(pkey, self._primary[pkey], key)
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
        return [KeyValue(pkey, self._primary[pkey]) for pkey in pkeys]

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
                yield KeyValue(pk, self._primary[pk], sk)

    def count(self, filter=None):
        if filter is None:
            return len(self._primary)
        gen, filters = genFilters(filter)
        return len(self.select_r(filter))

    def setBatch(self, records, notify=True):
        for r in records:
            self.set(r.key, r.value, notify)

    def setBatch_r(self, records, notify=True): 
        for r in records:
            self.set_r(r.key, r.value, notify)

    def pkeys(self, filter=None):
        return [kv.key for kv in self.select_r(filter)]
    
    def _index(self, pkey, data):
        for col, index in self._indices.iteritems():
            key = self._getIndexer(col).index_r(data)
            if key is None:
                continue
            if key not in index:
                index[key] = []
            if pkey not in index[key]:
                index[key].append(pkey)

    def _unindex(self, pkey, data):
        for col, index in self._indices.iteritems():
            key = self._getIndexer(col).index_r(data)
            if key in index and pkey in index[key]:
                index[key].remove(pkey)
                if len(index[key]) == 0:
                    del index[key]
                    
    def _erase(self):
        self._primary = {}
        self._indices = {}
        self._pkey = 0
        self._indexers = {}
        
    def _ensureIndex(self, unspec):
        spec = normalizeSpec(unspec)
        if spec not in self._indices:
            self._indices[spec] = index = {}
            indexer = self._getIndexer(spec)
            for pkey, data in self._primary.iteritems():
                key = indexer.index_r(data)
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
        return self._indices[normalizeSpec(spec)]

    def _put(self, data, notify=True):
        self._pkey += 4
        self._primary[self._pkey] = data
        self._index(self._pkey, data)
        if notify:
            self._save()
            info_r = KeyValueChange(self._pkey, data, None)
            self.notify('change_r', info_r)
            self.notify('key_r:%s' % self._pkey, info_r)
            info = lambda: KeyValueChange(self._pkey, decodes(data), None)
            self.notify('change', info)
            self.notify('key:%s' % self._pkey, info)

    def insert(self, records, notify=True):
        if type(records) is not list:
            records = [records]
        return self.insert_r(map(encodes, records), notify)

    def insert_r(self, records, notify=True):
        keys = []
        for r in records:
            self._put(r, notify)
            keys.append(self._pkey)
        return keys

    def set(self, pkey, data, notify=True):
        self.set_r(pkey, encodes(data), notify)
            
    def set_r(self, pkey, data, notify=True):
        old = self._primary.get(pkey)
        if old is not None:
            self._unindex(pkey, old)
        self._primary[pkey] = data
        self._index(pkey, data)
        if pkey > self._pkey:
            self._pkey = pkey
        if notify:
            self._save()
            info_r = KeyValueChange(pkey, data, old)
            self.notify('change_r', info_r)
            self.notify('key_r:%s' % pkey, info_r)
            info = lambda: KeyValueChange(pkey, decodes(data), old and decodes(old))
            self.notify('change', info)
            self.notify('key:%s' % pkey, info)

    def _update(self, pkey, values, vrec):
        rec = self.get(pkey)
        if updateFields(rec, values, vrec):
            self.set_r(pkey, encodes(rec))

    def update_r(self, filter, values, model=None):
        if model is not None:
            model = decodes(model)
        return self.update(filter, values, model)

    def update(self, filter, values, model=None):
        pkeys = []
        for kv in self.select_r(filter):
            rec = decodes(kv.value)
            if updateFields(rec, values, model):
                pkeys.append(kv.key)
                self.set_r(kv.key, encodes(rec))
        return pkeys

    def _pop(self, pkey, notify=True):
        try:
            data = self._primary[pkey]
        except KeyError:
            raise KeyError(pkey)
        self._unindex(pkey, data)
        del self._primary[pkey]
        if notify:
            self._save()
            info_r = KeyValueChange(pkey, None, data)
            self.notify('change_r', info_r)
            self.notify('key_r:%s' % pkey, info_r)
            info = lambda: KeyValueChange(pkey, None, decodes(data))
            self.notify('change', info)
            self.notify('key:%s' % pkey, info)
        return data

    def pop_r(self, filter=None, notify=True):
        kvs = self.select_r(filter)
        for kv in kvs:
            self._pop(kv.key, notify)
        return kvs

    def pop(self, filter=None, notify=True):
        kvs = self.select(filter)
        for kv in kvs:
            self._pop(kv.key, notify)
        return kvs

    def _removeAll(self):
        count = len(self._primary)
        info = KeyValueChange(-1, None, None)
        for pkey in list(self._primary):
            self._pop(pkey, notify=False)
            self.notify('key_r:%s' % pkey, info)
            self.notify('key:%s' % pkey, info)
        self._pkey = 0
        if count > 0:
            self._save()
            self.notify('change_r', KeyValueChange(-count, None, None))
            self.notify('change', KeyValueChange(-count, None, None))
        return count

    def remove(self, filter=None):
        if filter is None:
            return self._removeAll()
        to_remove = [item.key for item in self.select_r(filter)]
        for pkey in to_remove:
            self._pop(pkey)
        return len(to_remove)

    def _get(self, pkey, required):
        value = self._primary.get(pkey)
        if required and value is None:
            raise KeyError(pkey)
        return [] if value is None else [KeyValue(pkey, value)]

    def get_r(self, pkey):
        if int(pkey) not in self._primary:
            raise KeyError(pkey)
        return self._primary[pkey]

    def get(self, pkey):
        return decodes(self.get_r(pkey))

    def values_r(self, filter=None):
        return [pk.value for pk in self.select_r(filter)]

    def values(self, filter=None):
        return [pk.value for pk in self.select(filter)]

    def setKey(self, spec, message, replace=True):
        return self.setKey_r(spec, encodes(message), replace)

    def setKey_r(self, spec, message, replace=True):
        """Inserts or updates a record indexed by spec.

        If replace is False and a matching record already
        exists, the update is rejected and a key of -1 is returned.
        """
        indexer = self._getIndexer(spec)
        key = indexer.index_r(message)
        to_remove = [item.key for item in self._selectKey(spec, key)]
        if len(to_remove) > 0:
            if not replace:
                return -1
            for pkey in to_remove[1:]:
                self._pop(pkey)
            self.set_r(to_remove[0], message)
            return to_remove[0]
        else:
            return self.insert_r([message])[0]

    def _join(self, left, join, query, func):
        for lkv in left:
            self._join1(lkv.key, lkv.value, join, query, func)

    def _join_r(self, left, join, query, func):
        for lkv in left:
            self._join1(lkv.key, decodes(lkv.value), join, query, func)

    def _join1(self, l_pk, left, join, query, func):
        l_col, r_col, type = join.leftCol, join.rightCol, join.type
        if r_col != '#':
            r_col = ':' + r_col
        spec = '%s %s' % (r_col, type)
        limit = join.limit or sys.maxint
        try:
            key = l_pk if l_col == '#' else left[l_col]
        except (KeyError, AttributeError):
            to_join = []
        else:
            filters = [query, Range(0, limit)] if query is not None else [Range(0, limit)]
            to_join = self.select_r([Key(spec, key)] + filters)
        if not to_join and join.nulls:
            to_join.append(KeyValue(0, encodes({})))
        for kv in to_join:
            right = decodes(kv.value)
            func(l_pk, left, kv.key, right)

    def join_r(self, left, join, query, merge):
        results = []
        def buildJoin(s_pk, s_rec, r_pk, r_rec):
            out = mergeRecords(s_pk, s_rec, r_pk, r_rec, merge, {})
            results.append(KeyValue(s_pk, encodes(out)))
        self._join_r(left, join, query, buildJoin)
        return results

    def join(self, left, join, query, merge):
        results = []
        def buildJoin(s_pk, s_rec, r_pk, r_rec):
            out = mergeRecords(s_pk, s_rec, r_pk, r_rec, merge, {})
            results.append(KeyValue(s_pk, out))
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

    def updateIter_r(self, stream, join, query, values):
        count = [0]
        join.nulls = 0 # don't want any cases of r_pk not in the table.
        def doUpdate(s_pk, s_rec, r_pk, r_rec):
            self._update(r_pk, values, s_rec)
            count[0] += 1
        self._join_r(stream, join, query, doUpdate)
        return count[0]

    def maxPK(self):
        return max(self._primary)

    def _save(self):
        pass

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

# Pass as jc_opts={'hooks':JC_HOOKS} to RPCHandler
# so as to enable the JSONCodec to pass query instances
# as values.

JC_HOOKS = {}
JC_HOOKS['KeyValue'] = lambda _,args: KeyValue(*args)
JC_HOOKS['PKey'] = lambda _,args: PKey(*args)
JC_HOOKS['Key'] = lambda _,args: Key(*args)
JC_HOOKS['KeyRange'] = lambda _,args: KeyRange(*args)
JC_HOOKS['KeyPrefix'] = lambda _,args: KeyPrefix(*args)
JC_HOOKS['FieldValue'] = lambda _,args: FieldValue(*args)
JC_HOOKS['QTerm'] = lambda _,args: QTerm(*args)
