import weakref
import cjson
from traverse import traverse

class BoundMethod(object):
    def __init__(self, handler, data):
        self.handler = weakref.ref(handler)
        self.oid = data['o']
        self.method = data['m']

    def __call__(self, *args):
        h = self.handler()
        if h is None:
            return False
        return h.send('browser', self.oid, {'m':self.method, 'a':list(args)})

    def ext_encoding(self):
        return 'BoundMethod', {'o':self.oid, 'm':self.method}

def makeBoundMethod(rpc_handler, data):
    method = BoundMethod(rpc_handler, data)
    rpc_handler.refs.append(method)
    return method

class JSONCodec(object):
    hooks = {'BoundMethod': makeBoundMethod}

    def preEncodeFn(self, data):
        if isinstance(data, Exception):
            return [data.__class__.__name__, data.args]
        try:
            name, value = data.ext_encoding()
        except:
            return None
        return {'__ext__name_': name, '__ext__args_': value}

    def encode(self, rpc_handler, data):
        return cjson.encode(traverse(data, self.preEncodeFn))    

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
        return traverse(cjson.decode(message), postDecodeFn)

JSON_CODEC = JSONCodec()
