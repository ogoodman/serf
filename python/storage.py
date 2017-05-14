"""Dictionary of persistent objects."""

import weakref
from serf.serializer import encodes, decodes, SerializationError
from serf.po.file import File
from serf.ref import Ref
from serf.proxy import Proxy
from serf.util import randomString, importSymbol
from serf.synchronous import Synchronous

AUTO_MAKE = {
    'node_observer': 'serf.po.node_observer.NodeObserver'
}

Unique = []

def save_fn(that):
    """Place-holder for a _save method on a yet-to-be persisted object.

    When an object is stored or instantiated, this _save method will
    be replaced with a working save function.
    """
    pass

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
        storage = self.storage()
        if name == 'ref':
            return Ref(storage, data['path'], data.get('facet'))
        if name == 'inst':
            cls = importSymbol(storage.map_class(data['CLS']))
            data['#vat'] = storage
            data.update(storage.resources)
            # Check for version change.
            data_version = data.get('$version', 0)
            cls_version = getattr(cls, '_version', 0)
            if cls_version != data_version:
                cls._upgrade(data, data_version)
            args = [data.get(key.lstrip('_')) for key in cls.serialize]
            inst = cls(*args)
            if cls_version != data_version:
                # Ensure new nested serializables get correct _save hook.
                encodes(inst, self)
            if hasattr(cls, '_save'):
                inst._save = self.save
            return inst
        raise SerializationError(name)

    def record(self, inst):
        cls = type(inst)
        # Replace any instance having a slot somewhere with its Ref.
        ref = getattr(inst, 'ref', None)
        if type(ref) is Ref and ref._path != self.path:
            cls, inst = Ref, ref
        if cls is Ref:
            data = {'path': inst._path}
            if inst._facet:
                data['facet'] = inst._facet
            return 'ref', data
        if type(getattr(cls, 'serialize', None)) is tuple:
            data = getDict(inst)
            data['CLS'] = '%s.%s' % (cls.__module__, cls.__name__)
            version = getattr(cls, '_version', None)
            if version:
                data['$version'] = version
            if hasattr(cls, '_save'):
                inst._save = self.save
            return 'inst', data
        raise SerializationError(str(cls))

    def codec(self, type_id):
        return None, None

    def namedCodec(self, type_name):
        return None, None


class Storage(object):
    def __init__(self, store, cx_factory=None):
        self.store = store # stuff on disk
        self.cache = weakref.WeakValueDictionary()
        self.resources = {}
        self.make_context = StorageCtx if cx_factory is None else cx_factory
        self.node_id = None
        self.map_class = lambda c: c

    def __getitem__(self, path):
        # we get instantiated values
        if path in self.cache:
            return self.cache[path]
        ctx = self.make_context(self, path)
        obj = decodes(self.store[path], ctx)
        self._addRef(path, obj)
        if type(getattr(obj, 'ref', None)) is Ref:
            self.cache[path] = obj
        return obj

    def _addRef(self, path, svalue):
        if type(getattr(svalue, 'serialize', None)) is tuple:
            if type(getattr(svalue, 'ref', None)) is not Ref:
                svalue.ref = Ref(self, path)
                getattr(svalue, '_on_addref', lambda: None)()
                return True

    def setContextFactory(self, cx_factory):
        self.make_context = cx_factory

    def __setitem__(self, path, svalue):
        self.save(path, svalue)
        self._addRef(path, svalue)
        ref = getattr(svalue, 'ref', None)
        if type(ref) is Ref:
            if ref._path != path:
                svalue = ref
            self.cache[path] = svalue

    def save(self, path, svalue=Unique):
        if svalue is Unique:
            svalue = self.cache[path]
        ctx = self.make_context(self, path)
        self.store[path] = encodes(svalue, ctx)

    def __delitem__(self, path):
        del self.store[path]
        try:
            del self.cache[path]
        except KeyError:
            pass

    def __contains__(self, path):
        return path in self.store

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

class NameStore(object):
    def __init__(self, storage, name_store):
        self.storage = storage
        self.store = name_store

    def _autoMake(self, name):
        # This should only really be allowed to happen in the default vat.
        # Code in Node assumes that system names are in the default vat.
        if name not in AUTO_MAKE:
            return None
        cls = importSymbol(AUTO_MAKE[name])
        return self.storage.makeRef(cls(self.storage)) # Add default_vat_id here?

    def getn(self, name):
        ctx = self.storage.make_context(self.storage)
        try:
            return decodes(self.store[name], ctx)
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
            return self.storage.makeRef(value)
        assert False, 'Cannot turn %r into a ref' % value

    def setn(self, name, ref_or_value):
        ref = self._asRef(ref_or_value)
        ctx = self.storage.make_context(self.storage)
        self.store[name] = encodes(ref, ctx)

    def deln(self, name, erase=False):
        if erase:
            self.getn(name)._erase()
        del self.store[name]

def getDict(inst):
    return dict([(key.lstrip('_'), getattr(inst, key)) for key in inst.serialize
                 if not key.startswith('#')])

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
