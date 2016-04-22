import weakref
import json
from serf.traverse import traverse
from serf.proxy import Proxy
from serf.bound_method import BoundMethod

# A proxy comes with an arg of {'o':objId}

def makeProxy(vat, data):
    """Rehydrates an incoming Proxy."""
    return Proxy(data['n'], data['o'], vat)

def makeBoundMethod(vat, data):
    """Rehydrates an incoming BoundMethod."""
    method = BoundMethod(vat, data['o'], data['m'], data.get('n', 'browser'))
    vat.refs.append(method)
    return method

class JSONCodec(object):
    hooks = {
        'BoundMethod': makeBoundMethod,
        'Proxy': makeProxy}

    def preEncodeFn(self, data):
        if isinstance(data, Exception):
            return [data.__class__.__name__, data.args]
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
            return None
        return traverse(json.loads(message), postDecodeFn)

JSON_CODEC = JSONCodec()
