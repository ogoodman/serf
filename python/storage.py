"""Dictionary of persistent objects."""

from serf.serialize import encodes, decodes, SerializationError
from serf.po.file import File
from serf.ref import Ref
from serf.proxy import Proxy
from serf.util import randomString, importSymbol
from serf.synchronous import Synchronous

# This enables us to move serializable classes around.
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

class Storage(object):
    def __init__(self, store, vat_id='0', vat_map=None, rpc=None, t_model=None):
        self.store = store # stuff on disk
        self.vat_id = vat_id
        self.vat_map = vat_map
        self.rpc = rpc
        self.cache = {} # instantiated
        self.thread_model = Synchronous() if t_model is None else t_model

    def setVatMap(self, vat_map):
        self.vat_map = vat_map

    def _vatId(self, path):
        if self.vat_map is None:
            return self.vat_id
        return self.vat_map.getVatId(path)

    def __getitem__(self, path):
        # we get instantiated values
        if path not in self.cache:
            vat_id = self._vatId(path)
            if vat_id == self.vat_id:
                self._load(path)
            else:
                self.cache[path] = self.rpc.makeProxy(path)
        return self.cache[path]

    def _addRef(self, path, svalue):
        if type(getattr(svalue, 'serialize', None)) is tuple:
            if type(getattr(svalue, 'ref', None)) is not Ref:
                svalue.ref = Ref(self, path)

    def _load(self, path):
        save = lambda: self.save(path)
        def dec(name, data, lev):
            return self.decode(name, data, lev, save)
        self.cache[path] = decodes(self.store['caps/' + path], dec)
        self._addRef(path, self.cache[path])

    def __setitem__(self, path, svalue):
        self.save(path, svalue)
        self._addRef(path, svalue)
        ref = getattr(svalue, 'ref', None)
        if type(ref) is Ref and ref._path != path:
            svalue = ref
        self.cache[path] = svalue
        if self.vat_map is not None:
            self.vat_map.setVatId(path, self.vat_id)

    def save(self, path, svalue=Unique):
        if svalue is Unique:
            svalue = self.cache[path]
        save = lambda: self.save(path)
        def enc(inst, lev):
            return self.encode(inst, lev, path, save)
        self.store['caps/' + path] = encodes(svalue, enc)

    def __delitem__(self, path):
        del self.store['caps/' + path]
        try:
            del self.cache[path]
        except KeyError:
            pass

    def clearCache(self):
        self.cache = {}

    def decode(self, name, data, lev, save=None):
        if name == 'ref':
            if 'node' in data:
                return self.rpc.makeProxy(data['path'], data['node'])
            # FIXME: should be a proxy if vatId(path) is not ours.
            return Ref(self, data['path'], data.get('facet'))
        if name == 'inst':
            cls = importSymbol(mapClass(data['CLS']))
            data['_vat'] = self
            args = [data.get(key) for key in cls.serialize]
            inst = cls(*args)
            if hasattr(cls, '_save'):
                inst._save = save
            return inst
        raise SerializationError(name)

    def encode(self, inst, lev, path=None, save=None):
        t = type(inst)
        # Replace any instance having a slot somewhere with its Ref.
        ref = getattr(inst, 'ref', None)
        if type(ref) is Ref and ref._path != path:
            t, inst = Ref, ref
        if t is Ref:
            data = {'path': inst._path}
            if inst._facet:
                data['facet'] = inst._facet
            return 'ref', data
        if t is Proxy:
            # FIXME: need not save node if node_id is ours.
            return 'ref', {'path': inst._path, 'node': inst._node}
        if type(getattr(t, 'serialize', None)) is tuple:
            data = getDict(inst)
            cls = inst.__class__
            data['CLS'] = '%s.%s' % (cls.__module__, cls.__name__)
            if hasattr(cls, '_save'):
                inst._save = save
            return 'inst', data
        raise SerializationError(str(t))

    def _autoMake(self, name):
        # This should only really be allowed to happen in the default vat.
        # Code in Node assumes that system names are in the default vat.
        if name not in AUTO_MAKE:
            return None
        cls = importSymbol(AUTO_MAKE[name])
        return self.makeRef(cls(self)) # Add default_vat_id here?

    def getn(self, name):
        try:
            return decodes(self.store['names/' + name], self.decode)
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
        def enc(inst, lev):
            return self.encode(inst, lev, '')
        self.store['names/' + name] = encodes(ref, enc)

    def deln(self, name, erase=False):
        if erase:
            self.getn(name)._erase()
        del self.store['names/' + name]

    def getRef(self, path):
        return Ref(self, path)

    def makeRef(self, svalue=None, vat_id=None):
        if vat_id in (None, self.vat_id):
            ref = Ref(self, randomString())
            if svalue is not None:
                ref._set(svalue)
        else:
            ref = self.rpc.makeProxy(randomString())
            self.vat_map.setVatId(ref._path, vat_id)
            if svalue is not None:
                self.save(ref._path, svalue)
                # could put proxy into cache here.
        return ref

    def makeProxy(self, path, node=None):
        return self.rpc.makeProxy(path, node)

    def makeFile(self, ref=False):
        file = File(self, randomString())
        if ref:
            r = Ref(self, file.path)
            r._set(file)
            return r
        return file

def getDict(inst):
    return dict([(key, getattr(inst, key)) for key in inst.serialize
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
