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
        return h.send_json({'o':self.oid, 'm':self.method, 'a':list(args)})

    def ext_encoding(self):
        return 'BoundMethod', {'o':self.oid, 'm':self.method}

class RPCHandler(object):
    def __init__(self, transport):
        self.transport = transport
        transport.subscribe('message', self.on_message)

        self.obj = {}
        self.hooks = {'BoundMethod': RPCHandler.makeBoundMethod}

        # Keep references alive because Publisher.subscribe does not.
        self.remote_subs = []

    def provide(self, name, obj):
        self.obj[name] = obj

    def makeBoundMethod(self, data):
        method = BoundMethod(self, data)
        self.remote_subs.append(method)
        return method

    def preEncodeFn(self, data):
        try:
            name, value = data.ext_encoding()
        except:
            return None
        return {'__ext__name_': name, '__ext__args_': value}

    def postDecodeFn(self, data):
        if type(data) is dict and '__ext__name_' in data:
            try:
                name, value = data['__ext__name_'], data['__ext__args_']
            except:
                return None
            if name in self.hooks:
                return self.hooks[name](self, value)
        return None

    def send_json(self, data):
        try:
            print self.transport.client_ip, 'Out', data
            json = traverse(data, self.preEncodeFn)
            self.transport.send('browser', cjson.encode(json))
        except Exception, e:
            print self.transport.client_ip, 'Not sent:', e, json
            return False

    def on_message(self, e, message):
        id = None
        try:
            data = traverse(cjson.decode(message['message']), self.postDecodeFn)
            print self.transport.client_ip, 'In', data
            id = data.get('i')
            o_id = data['o']
            try:
                obj = self.obj[o_id]
            except KeyError:
                if id is not None:
                    self.send_json({'i': id, 'e': ['NameError', 'no such object: %r' % o_id]})
                return
            m_name = data['m']
            if m_name.startswith('_'):
                if id is not None:
                    self.send_json({'i': id, 'e': ['AttributeError', '%r is not public' % m_name]})
                return
            method = getattr(obj, m_name)
            args = data['a']
            r = method(*args)
        except Exception, e:
            if id is not None:
                e_name = e.__class__.__name__
                e_args = e.args
                self.send_json({'i': id, 'e': [e.__class__.__name__, e.args]})
        else:
            if id is not None:
                if r is None:
                    self.send_json({'i': id})
                else:
                    self.send_json({'i': id, 'r': r})
