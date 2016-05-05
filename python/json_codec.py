import weakref
import json
from serf.traverse import traverse
from serf.ref import Ref
from serf.proxy import Proxy
from serf.bound_method import BoundMethod
from serf.util import importSymbol
from serf.serializer import SerializationError

# A proxy comes with an arg of {'o':objId}

def makeProxy(vat, data):
    """Rehydrates an incoming Proxy."""
    node, path = data['n'], data['o']
    if node == vat.node_id and path in vat.storage:
        return vat.storage[path]
    proxy = Proxy(data['n'], data['o'], vat)
    vat.refs.append(proxy)
    return proxy

def makeBoundMethod(vat, data):
    """Rehydrates an incoming BoundMethod."""
    method = BoundMethod(vat, data['o'], data['m'], data.get('n', 'browser'))
    vat.refs.append(method)
    return method

DEFAULT_HOOKS = {
    'BoundMethod': makeBoundMethod,
    'Proxy': makeProxy,
}

class JSONCodec(object):
    """Codec used by RPCHandler for JSON protocol calls.

    This is strongly coupled to RPCHandler; there is no other kind
    of object which it would be reasonable to pass as the rpc member.
    """
    def __init__(self, rpc, hooks=None, safe=None, auto_proxy=False):
        self.rpc = weakref.ref(rpc)
        self.auto_proxy = auto_proxy
        self.node_id = rpc.node_id
        self.hooks = dict(DEFAULT_HOOKS)
        self.hooks.update(hooks or {})
        self.safe = safe or []

    def _safe_cls(self, cls):
        for prefix in self.safe:
            if cls.startswith(prefix):
                return True
        return False

    def _autoProxy(self, obj):
        """Store persistent objects in rpc.storage and return a Proxy."""
        ref = getattr(obj, 'ref', None)
        if type(ref) is not Ref:
            return None
        # FIXME: need to make prefix depend on the vat so as to avoid
        # ambiguous paths when objects come from multiple vats.
        path = 'vat:' + ref._path
        store = self.rpc().storage
        if path in store:
            assert store[path] is obj, 'Ambiguous path issues'
        else:
            store[path] = obj
        # JSON codec encoding for a Proxy(ref._node, ref._path)
        value = dict(n=self.node_id, o=path)
        return {'__ext__name_': 'Proxy', '__ext__args_': value}

    def preEncodeFn(self, data):
        cls = data.__class__

        if isinstance(data, Exception):
            return [cls.__name__, data.args]

        if self.auto_proxy:
            result = self._autoProxy(data)
            if result is not None:
                return result

        serialize = getattr(cls, 'serialize', None)
        if type(serialize) is tuple:
            name = cls.__name__
            value = []
            for key in serialize:
                if key.startswith('_'):
                    return None # requires local capabilities
                value.append(getattr(data, key, None))
        else:
            try:
                name, value = data._ext_encoding()
            except:
                return None
        return {'__ext__name_': name, '__ext__args_': value}

    def encode(self, data):
        return json.dumps(traverse(data, self.preEncodeFn))

    def postDecodeFn(self, data):
        if type(data) is dict and '__ext__name_' in data:
            try:
                name, value = data['__ext__name_'], data['__ext__args_']
            except:
                return None

            # FIXME: have we set up the full serializability code
            # below only to use hooks here instead for stuff like QTerm?

            if name in self.hooks:
                return self.hooks[name](self.rpc(), value)

            if self._safe_cls(name):
                cls = importSymbol(name)
                try:
                    args = [value[key] for key in cls.serialize]
                except KeyError:
                    raise SerializationError(name + ': ' + repr(data))
                else:
                    return cls(*args)

        return None

    def decode(self, message):
        return traverse(json.loads(message), self.postDecodeFn)
