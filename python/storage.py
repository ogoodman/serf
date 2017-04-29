"""Dictionary of persistent objects."""

import weakref
from serf.serializer import encodes, decodes, SerializationError
from serf.po.file import File
from serf.ref import Ref
from serf.proxy import Proxy
from serf.util import randomString, importSymbol
from serf.synchronous import Synchronous

# This enables us to move serializable classes around.
# FIXME: this is a bad way to do it because it assumes that
# serf.config is owned by the application.
try:
    from serf.config import mapClass
except ImportError:
    mapClass = lambda c: c

AUTO_MAKE = {
    'node_observer': 'serf.po.node_observer.NodeObserver'
}

Unique = []

class NoSuchName(Exception):
    pass

class StorageCtx(object):
    def __init__(self, storage, path=None):
        self.storage = weakref.ref(storage)
        self.path = path

    def save(self):
        if self.path is not None:
            storage = self.storage()
            if storage is not None:
                storage.save(self.path)

    def custom(self, name, data):
        if name == 'ref':
            return Ref(self.storage(), data['path'], data.get('facet'))
        if name == 'inst':
            cls = importSymbol(mapClass(data['CLS']))
            data['_vat'] = self.storage()
            data.update(self.storage().resources)
            args = [data.get(key) for key in cls.serialize]
            inst = cls(*args)
            if hasattr(cls, '_save'):
                inst._save = self.save
            return inst
        raise SerializationError(name)

    def record(self, inst):
        t = type(inst)
        # Replace any instance having a slot somewhere with its Ref.
        ref = getattr(inst, 'ref', None)
        if type(ref) is Ref and ref._path != self.path:
            t, inst = Ref, ref
        if t is Ref:
            data = {'path': inst._path}
            if inst._facet:
                data['facet'] = inst._facet
            return 'ref', data
        if type(getattr(t, 'serialize', None)) is tuple:
            data = getDict(inst)
            cls = inst.__class__
            data['CLS'] = '%s.%s' % (cls.__module__, cls.__name__)
            if hasattr(cls, '_save'):
                inst._save = self.save
            return 'inst', data
        raise SerializationError(str(t))

    def codec(self, type_id):
        return None, None

    def namedCodec(self, type_name):
        return None, None


class Storage(object):
    def __init__(self, store, cx_factory=None):
        self.store = store # stuff on disk
        self.cache = {} # instantiated
        self.resources = {}
        self.make_context = StorageCtx if cx_factory is None else cx_factory

    def __getitem__(self, path):
        # we get instantiated values
        if path not in self.cache:
            self._load(path)
        return self.cache[path]

    def _addRef(self, path, svalue):
        if type(getattr(svalue, 'serialize', None)) is tuple:
            if type(getattr(svalue, 'ref', None)) is not Ref:
                svalue.ref = Ref(self, path)
                getattr(svalue, '_on_addref', lambda: None)()

    def setContextFactory(self, cx_factory):
        self.make_context = cx_factory

    def _load(self, path):
        ctx = self.make_context(self, path)
        self.cache[path] = decodes(self.store['caps/' + path], ctx)
        self._addRef(path, self.cache[path])

    def __setitem__(self, path, svalue):
        self.save(path, svalue)
        self._addRef(path, svalue)
        ref = getattr(svalue, 'ref', None)
        if type(ref) is Ref and ref._path != path:
            svalue = ref
        self.cache[path] = svalue

    def save(self, path, svalue=Unique):
        if svalue is Unique:
            svalue = self.cache[path]
        ctx = self.make_context(self, path)
        self.store['caps/' + path] = encodes(svalue, ctx)

    def __delitem__(self, path):
        del self.store['caps/' + path]
        try:
            del self.cache[path]
        except KeyError:
            pass

    def __contains__(self, path):
        return ('caps/' + path) in self.store

    def clearCache(self):
        self.cache = {}

    def _autoMake(self, name):
        # This should only really be allowed to happen in the default vat.
        # Code in Node assumes that system names are in the default vat.
        if name not in AUTO_MAKE:
            return None
        cls = importSymbol(AUTO_MAKE[name])
        return self.makeRef(cls(self)) # Add default_vat_id here?

    def getn(self, name):
        ctx = self.make_context(self)
        try:
            return decodes(self.store['names/' + name], ctx)
        except KeyError:
            pass
        ref = self._autoMake(name)
        if ref is None:
            raise NoSuchName(name)
        self.setn(name, ref)
        return ref

    def _asRef(self, value):
        if type(value) in (Ref, Proxy):
            return value
        if type(getattr(value, 'ref', None)) is Ref:
            return value.ref
        if type(getattr(value, 'serialize', None)) is tuple:
            return self.makeRef(value)
        assert False, 'Cannot turn %r into a ref' % value

    def setn(self, name, ref_or_value):
        ref = self._asRef(ref_or_value)
        ctx = self.make_context(self)
        self.store['names/' + name] = encodes(ref, ctx)

    def deln(self, name, erase=False):
        if erase:
            self.getn(name)._erase()
        del self.store['names/' + name]

    def getRef(self, path):
        return Ref(self, path)

    def makeRef(self, svalue=None, vat_id=None):
        ref = Ref(self, randomString())
        if svalue is not None:
            ref._set(svalue)
        return ref

    def makeFile(self, ref=False):
        file = File(self, randomString())
        if ref:
            r = Ref(self, file.path)
            r._set(file)
            return r
        return file

def getDict(inst):
    prefix = '_' if getattr(inst.__class__, '_private', False) else ''
    return dict([(key, getattr(inst, prefix + key)) for key in inst.serialize
                 if not key.startswith('_')])

def _str(inst, lev=0):
    ind = '  ' * lev
    typ = type(inst)
    if typ.__name__ == 'REPLProxy':
        inst = inst.target
        typ = type(inst)
    if lev > 0 and type(inst) is Ref:
        return 'ref(path=%r)' % inst._path
    if typ is Proxy:
        return 'ref(path=%r, node=%r)' % (inst._path, inst._node)
    if type(getattr(inst, 'serialize', None)) is tuple:
        if type(inst) is Ref:
            inst = inst._get()
        data = getDict(inst)
        nvp = ['%s=%s' % (k, _str(v, lev+1)) for k, v in data.items()]
        name = inst.__class__.__name__
        if len(data) == 0:
            return '%s()' % name
        if len(data) == 1:
            return '%s(%s)' % (name, nvp[0])
        return '%s(\n%s  %s)' % (name, ind, ('\n%s  ' % ind).join(nvp))
    if typ is tuple:
        return '(%s)' % ', '.join([_str(x, lev+1) for x in inst])
    if typ is list:
        return '[%s]' % ', '.join([_str(x, lev+1) for x in inst])
    if typ is dict:
        nvp = ['%r: %s' % (k, _str(v, lev+1)) for k, v in inst.items()]
        return '{%s}' % ', '.join(nvp)
    if typ is Ref:
        return 'ref(path=%r)' % inst._path
    return str(inst)

def fcat(inst):
    print _str(inst)
