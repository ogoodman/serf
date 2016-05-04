import weakref
import json
from serf.traverse import traverse
from serf.proxy import Proxy
from serf.bound_method import BoundMethod
from serf.util import importSymbol
from serf.serializer import SerializationError

# A proxy comes with an arg of {'o':objId}

def makeProxy(vat, data):
    """Rehydrates an incoming Proxy."""
    proxy = Proxy(data['n'], data['o'], vat)
    vat.refs.append(proxy)
    return proxy

def makeBoundMethod(vat, data):
    """Rehydrates an incoming BoundMethod."""
    method = BoundMethod(vat, data['o'], data['m'], data.get('n', 'browser'))
    vat.refs.append(method)
    return method

class JSONCodec(object):
    hooks = {
        'BoundMethod': makeBoundMethod,
        'Proxy': makeProxy}

    safe = ['serf.tables']

    def _safe_cls(self, cls):
        for prefix in self.safe:
            if cls.startswith(prefix):
                return True
        return False

    def preEncodeFn(self, data):
        cls = data.__class__

        if isinstance(data, Exception):
            return [cls.__name__, data.args]

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

    def encode(self, rpc_handler, data):
        return json.dumps(traverse(data, self.preEncodeFn))

    def decode(self, rpc_handler, message):
        def postDecodeFn(data):
            if type(data) is dict and '__ext__name_' in data:
                try:
                    name, value = data['__ext__name_'], data['__ext__args_']
                except:
                    return None
                if name in self.hooks:
                    return self.hooks[name](rpc_handler, value)

                if self._safe_cls(name):
                    cls = importSymbol(name)
                    try:
                        args = [value[key] for key in cls.serialize]
                    except KeyError:
                        raise SerializationError(name + ': ' + repr(data))
                    else:
                        return cls(*args)
            return None
        return traverse(json.loads(message), postDecodeFn)

JSON_CODEC = JSONCodec()
