"""Another attempt to model persistence."""

from cStringIO import StringIO
from serf.serialize import encode, decode, encodes, decodes, SerializationError, POD_TYPES
from serf.ref import Ref
from serf.synchronous import Synchronous
from serf.util import randomString, rmap
from serf.proxy import Proxy
from serf.storage import Storage

# Most of what happens here is converting stuff, either for
# passing it to another Vat or for saving to disk.
#
# There are 3 cases (2 directions each):
# 1. to/from disk storage
# 2. to/from Vat in different thread
# 3. to/from remote Vat (via network)
#
# There are a few different types being passed around:
# 1. plain-old-data
# 2. references / proxies
# 3. capability instances
#
# Actually 3 is not passed but converted to references.
# Incoming references to local objects should be converted to
# direct (Python language) references to those objects.

EXCEPTIONS = {
    'TypeError': TypeError,
    'AttributeError': AttributeError,
}

def perr(*args):
    print args

def convert(v1, v2, value):
    if v1.node_id == v2.node_id:
        return v2.localize(v1.delocalize(value))
    return decodes(encodes(value, v1.encodeRemote), v2.decodeRemote)

class RemoteException(Exception):
    pass

class NoSuchObject(Exception):
    pass

class NoSuchName(Exception):
    pass

class SendErrorCb(object):
    def __init__(self, vat, sender_cb_id):
        self.vat = vat
        self.cb_id = sender_cb_id

    def failure(self, exc):
        self.vat.put('R', self.cb_id, {'exc': exc})

class Vat(object):
    def __init__(self, node_id, vat_id, storage, node=None, t_model=None):
        thread_model = Synchronous() if t_model is None else t_model
        self.storage = storage
        self.node_id = node_id
        self.vat_id = vat_id
        self.node = node
        self.callbacks = {}
        self.thread_model = thread_model

    def setNode(self, node):
        self.node = node

    def makeProxy(self, path, node=None):
        return Proxy(node or self.node_id, path, self)

    def decodeRemote(self, name, data, lev):
        if name == 'ref':
            node = data['node']
            if node == self.node_id:
                return Ref(self.storage, data['path'])
            return Proxy(node, data['path'], self)
        if name == 'exc':
            try:
                cls = EXCEPTIONS[data['type']]
            except:
                return RemoteException('%s%r' % (data['type'], data['args']))
            return cls(*data['args'])
        raise SerializationError(name)

    def encodeRemote(self, inst, lev):
        t = type(inst)
        if isinstance(inst, Exception):
            return 'exc', {'type': t.__name__, 'args': inst.args}
        ref = getattr(inst, 'ref', None)
        if type(ref) is Ref:
            t, inst = Ref, ref
        if t is Ref and not inst._facet:
            # TODO: make a slot property for storing facet ref slots.
            return 'ref', {'path': inst._path, 'node': self.node_id}
        if t is Proxy:
            return 'ref', {'path': inst._path, 'node': inst._node}
        raise SerializationError(str(t))

    def put(self, what, addr, msg):
        if what == 'n':
            func = self.nhandle
        elif what == 'r':
            func = self.rhandle
        elif what == 'R':
            func = self.handleReply
        self.thread_model.callFromThread(func, addr, msg)

    def nhandle(self, addr, msg):
        # call from event loop, pulling from a queue
        msg = rmap(self.localize, msg)
        self._handle(addr, msg)

    def rhandle(self, addr, msg_data):
        # call from event loop, pulling from a queue
        msg = decode(msg_data, self.decodeRemote)
        self._handle(addr, msg)

    def _handle(self, addr, msg):
        if 'method' in msg:
            # make a green thread to run this call
            self.thread_model.call(self.handleCall, addr, msg)
        else:
            self.handleReply(addr, msg)

    def handleReply(self, addr, msg):
        cb = self.callbacks.pop(addr)
        if 'result' in msg:
            cb.success(msg['result'])
        else:
            cb.failure(msg['exc'])

    def handleCall(self, addr, msg):
        method = msg['method']
        args = msg['args']
        exc = None
        if addr:
            try:
                obj = self.storage[addr]
            except KeyError:
                exc = NoSuchObject(addr)
            else:
                try:
                    result = getattr(obj, method)(*args)
                except Exception, exc:
                    pass
        else:
            # Empty addr string can be used to ping the node.
            result = None
        try:
            reply_addr = msg['reply_addr']
            reply_node = msg['reply_node']
        except KeyError:
            if exc is not None:
                print 'Exc (no reply addr):', addr, msg, exc
            return
        if exc is None:
            msg = {'result': result}
        else:
            msg = {'exc': exc}
        try:
            # serialization errors can occur here.
            self.send(reply_node, reply_addr, msg)
        except SerializationError, exc:
            self.send(reply_node, reply_addr, {'exc': exc})

    def send(self, node, addr, msg, errh=None):
        if node == self.node_id:
            msg = rmap(self.delocalize, msg)
            self.node.nsend(addr, msg)
        else:
            f = StringIO()
            encode(f, addr)
            encode(f, msg, self.encodeRemote)
            self.node.send(node, f.getvalue(), errh=errh)

    def provide(self, addr, obj):
        self.storage[addr] = obj
        return Proxy(self.node_id, addr, self)

    def call(self, node, addr, method, args):
        cb = self.thread_model.makeCallback()
        reply_addr = '@' + self.vat_id + '/' + randomString()
        self.callbacks[reply_addr] = cb
        msg = {'method': method,
               'args': args,
               'reply_addr': reply_addr,
               'reply_node': self.node_id}
        send_err_cb = SendErrorCb(self, reply_addr)
        self.send(node, addr, msg, send_err_cb.failure)
        return cb

    def localize(self, x):
        if isinstance(x, Exception):
            return x
        typ = type(x)
        if typ in POD_TYPES:
            return x
        if typ is Proxy:
            if x._node == self.node_id:
                return Ref(self.storage, x._path)
            return Proxy(x._node, x._path, self)
        raise SerializationError('cannot localize type %s' % typ)

    def delocalize(self, x):
        # This is what we call for sending things to a different thread.
        # It is only applied to leaf nodes (via rmap).
        # rmap copies but it should actually be possible to change
        # only the leaf nodes that need to change because while a call
        # is in progress nothing can happen to variables referenced
        # only in the suspended stack-frame. If variables are added to
        # self then it would be possible for a call to access them
        # from the original vat's thread at the same time that they are
        # being accessed in the other thread.
        if isinstance(x, Exception):
            return x
        typ = type(x)
        if typ in POD_TYPES:
            return x
        if typ is Proxy:
            return Proxy(x._node, x._path)
        if typ is not Ref:
            try:
                ref = x.ref
            except AttributeError:
                pass
            else:
                # Should we be checking in case ref is not a Ref?
                if type(ref) is Ref:
                    x = ref
                    typ = Ref
                else:
                    print 'unexpected .ref attribute', repr(x), x.ref
        if typ is Ref:
            return Proxy(self.node_id, x._path)
        raise SerializationError('cannot delocalize type %s' % typ)

    def setVatMap(self, vat_map):
        self.storage.setVatMap(vat_map)
