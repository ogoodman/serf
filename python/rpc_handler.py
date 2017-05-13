"""Another attempt to model persistence."""

import weakref
from cStringIO import StringIO
from serf.serializer import encode, decode, encodes, decodes, SerializationError, POD_TYPES
from serf.ref import Ref
from serf.synchronous import Synchronous
from serf.util import randomString, rmap, importSymbol
from serf.proxy import Proxy
from serf.storage import StorageCtx
from serf.json_codec import JSON_CODEC
from serf.bound_method import JCBoundMethod


# Most of what happens here is converting stuff, either for
# passing it to another RPCHandler or for saving to disk.
#
# There are 3 cases (2 directions each):
# 1. to/from disk storage
# 2. to/from RPCHandler in different thread
# 3. to/from remote RPCHandler (via network)
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
        self.vat.lput(self.cb_id, {'e': exc})

def encodeException(e):
    return [type(e).__name__] + list(e.args)

def decodeException(e):
    try:
        return EXCEPTIONS[e[0]](*e[1:])
    except:
        return RemoteException('%s%r' % (e[0], e[1:]))


class RemoteCtx(object):
    def __init__(self, vat, msg_data=None):
        self.vat = weakref.ref(vat)
        self.node_id = vat.node_id
        self.safe = vat.safe
        self.msg_data = msg_data or {}

    def _safe_cls(self, cls):
        for prefix in self.safe:
            if cls.startswith(prefix):
                return True
        return False

    def custom(self, name, data):
        if name == 'ref':
            node = data['node']
            if node == self.node_id:
                return Ref(self.vat().storage, data['path'])
            if node == '-':
                node = self.msg_data.get('from')
            return Proxy(node, data['path'], self.vat())
        if name == 'exc':
            return decodeException(data)

        if name == 'inst' and self._safe_cls(data['CLS']):
            cls = importSymbol(data['CLS'])
            try:
                args = [data[key.lstrip('_')] for key in cls.serialize]
            except KeyError:
                raise SerializationError(name + ': ' + repr(data))
            else:
                return cls(*args)

        raise SerializationError(name)

    def record(self, inst):
        t = type(inst)
        if isinstance(inst, Exception):
            return 'exc', encodeException(inst)
        ref = getattr(inst, 'ref', None)
        if type(ref) is Ref:
            t, inst = Ref, ref
        if t is Ref and not inst._facet:
            # TODO: make a slot property for storing facet ref slots.
            return 'ref', {'path': inst._path, 'node': self.node_id}
        if t is Proxy:
            return 'ref', {'path': inst._path, 'node': inst._node}

        # Serialize instances without any capability members.
        s_attrs = getattr(t, 'serialize', None)
        if type(s_attrs) is tuple and not [a for a in s_attrs if a.startswith('_')]:
            data = dict([(key.lstrip('_'), getattr(inst, key)) for key in s_attrs])
            cls = inst.__class__
            data['CLS'] = '%s.%s' % (cls.__module__, cls.__name__)
            return 'inst', data

        raise SerializationError(str(t))

    def codec(self, type_id):
        return None

    def namedCodec(self, type_name):
        return None, None

class RPCStorageCtx(StorageCtx):
    def __init__(self, rpc, storage, path=None):
        StorageCtx.__init__(self, storage, path)
        self.rpc = rpc

    def custom(self, name, data):
        if name == 'ref' and 'node' in data:
            return self.rpc.makeProxy(data['path'], data['node'])
        return StorageCtx.custom(self, name, data)

    def record(self, inst):
        if type(inst) is Proxy:
            return 'ref', {'path': inst._path, 'node': inst._node}
        return StorageCtx.record(self, inst)

# JSONCodec context class for RPCHandler.

def makeProxy(vat, data):
    """Rehydrates an incoming Proxy."""
    node, path = data.get('n', 'browser'), data['o']
    if node == vat.node_id and path in vat.storage:
        return vat.storage[path]
    proxy = Proxy(node, path, vat)
    vat.refs.append(proxy)
    return proxy

def makeBoundMethod(vat, data):
    """Rehydrates an incoming JCBoundMethod."""
    method = JCBoundMethod(vat, data['o'], data['m'], data.get('n', 'browser'))
    vat.refs.append(method)
    return method

DEFAULT_HOOKS = {
    'BoundMethod': makeBoundMethod,
    'Proxy': makeProxy,
}

class JSONCodecCtx(object):
    def __init__(self, rpc, hooks=None, safe=None, auto_proxy=False):
        self.rpc = weakref.ref(rpc)
        if auto_proxy is False:
            self.auto_proxy = None
        elif auto_proxy is True:
            self.auto_proxy = self._autoProxyPath
        else:
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

    def custom(self, name, value):
        # FIXME: have we set up the full serializability code
        # below only to use hooks here instead for stuff like QTerm?

        if name in self.hooks:
            return self.hooks[name](self.rpc(), value)

        if not self._safe_cls(name):
            raise SerializationError('Unsafe type: ' + name)

        cls = importSymbol(name)
        try:
            args = [value[key] for key in cls.serialize]
        except KeyError:
            raise SerializationError(name + ': ' + repr(data))
        else:
            return cls(*args)

    def _autoProxyPath(self, obj):
        ref = getattr(obj, 'ref', None)
        if type(ref) is not Ref:
            return None
        # FIXME: need to make prefix depend on the vat so as to avoid
        # ambiguous paths when objects come from multiple vats.
        return 'vat:' + ref._path

    def _autoProxy(self, path, obj):
        """Store persistent objects in rpc.storage and return a Proxy."""
        store = self.rpc().storage
        if path in store:
            assert store[path] is obj, 'Ambiguous path issues'
        else:
            store[path] = obj
        # JSON codec encoding for a Proxy(ref._node, ref._path)
        value = dict(n=self.node_id, o=path)
        return 'Proxy', value

    def record(self, data):
        cls = data.__class__

        if self.auto_proxy is not None:
            path = self.auto_proxy(data)
            if path is not None:
                return self._autoProxy(path, data)

        ref = getattr(data, 'ref', None)
        if type(ref) is Ref:
            data = ref

        if hasattr(data, '_ext_encoding'):
            return data._ext_encoding()

        serialize = getattr(cls, 'serialize', None)
        if type(serialize) is tuple:
            name = cls.__name__
            value = []
            for key in serialize:
                if key.startswith('#'):
                    raise SerializationError('local resources used: ' + cls.__name__)
                value.append(getattr(data, key, None))
            return name, value

        raise SerializationError('cannot serialize: ' + cls.__name__)


class RPCHandler(object):
    """Exposes a dictionary of objects for remote procedure calls.

    Calls are received by subscribing to the transport's 'message' event.
    Responses are sent using transport.send.

    A codec for messages is selected depending on the protocol indicated
    by transport for the incoming message.

    :param transport: implementation of Transport
    :param storage: dictionary-like collection of objects
    :param t_model: a thread model
    :param verbose: whether to print debugging output
    :param jc_opts: options for the JSONCodec
    """
    def __init__(self, transport, storage, t_model=None, verbose=False, jc_opts=None):
        thread_model = Synchronous() if t_model is None else t_model
        self.storage = storage
        self.node_id = transport.node_id
        self.vat_id = transport.path
        self.node = transport
        self.callbacks = {}
        self.thread_model = thread_model
        self.verbose = verbose
        self.safe = []
        transport.subscribe('message', self.handle)
        transport.subscribe('online', self._notifyNodeObserver)
        transport.subscribe('connected', self._notifyNodeObserver)
        self.refs = []
        if hasattr(storage, 'setContextFactory'):
            rpc = weakref.proxy(self)
            def makeStorageCtx(storage, path=None):
                return RPCStorageCtx(rpc, storage, path)
            storage.setContextFactory(makeStorageCtx)
            # NOTE: this is for the node observer.
            storage.getRPC = lambda: rpc
        self.remote_ctx = RemoteCtx(self)
        self.json_ctx = JSONCodecCtx(self, **(jc_opts or {}))

    def makeProxy(self, path, node=None):
        return Proxy(node or self.node_id, path, self)

    def handle(self, ev, msg):
        """Handler for encoded message data.

        Args:
            ev: the event (not used)
            msg: message event object
        """
        self.thread_model.callFromThread(self._rhandle, msg)

    def lput(self, addr, msg):
        """Handler for messages staying on this node.

        Messages are not encoded. They may be going from one
        RPCHandler to another so localize is called to convert Refs to
        Proxies and vice-versa.

        Args:
            addr: instance to which message is addressed
            msg: python data (not encoded)
        """
        self.thread_model.callFromThread(self._nhandle, addr, msg)

    def _nhandle(self, addr, msg):
        msg = rmap(self.localize, msg)
        self._handle(addr, msg, self.node_id)

    def _peer_protocol(self, node):
        if node in ('server', 'browser'):
            return 'json'
        if node == self.node_id:
            return 'local'
        return 'serf'

    def _rhandle(self, msg_data):
        from_ = msg_data['from']
        pcol = self._peer_protocol(from_)
        if pcol == 'json':
            msg = JSON_CODEC.decode(msg_data['message'], self.json_ctx)
            if self.verbose:
                print getattr(self.node, 'client_ip', ''), 'In', msg
        elif pcol == 'local':
            msg = rmap(self.localize, msg_data['message'])
        else:
            f = StringIO(msg_data['message'])
            msg = decode(f, RemoteCtx(self, msg_data))
        addr = msg['o']
        # Subtract transport path from incoming message.
        assert(addr.startswith(self.node.path))
        addr = addr[len(self.node.path):]
        self._handle(addr, msg, from_)

    def _handle(self, addr, msg, from_):
        if 'm' in msg:
            self.thread_model.call(self.handleCall, addr, msg, from_)
        else:
            self.handleReply(addr, msg)

    def handleReply(self, addr, msg):
        # TODO: make from-node part of the callbacks key and pass it through.
        cb = self.callbacks.pop(addr)
        if 'r' in msg:
            cb.success(msg['r'])
        else:
            if type(msg['e']) is list:
                msg['e'] = decodeException(msg['e'])
            cb.failure(msg['e'])

    def localCall(self, addr, method, args):
        result, exc = None, None
        if addr:
            try:
                obj = self.storage[addr]
            except KeyError:
                exc = NoSuchObject(addr)
            else:
                try:
                    # FIXME: rpc_handler made _methods private. Should we?
                    if method == '__call__':
                        result = obj(*args)
                    else:
                        result = getattr(obj, method)(*args)
                except Exception, exc:
                    pass
        return result, exc

    def handleCall(self, addr, msg, reply_node):
        method = msg['m']
        args = msg['a']
        result, exc = self.localCall(addr, method, args)
        try:
            reply_addr = msg['O']
        except KeyError:
            if exc is not None:
                print 'Exc (no reply addr):', addr, msg, exc
            return
        if exc is None:
            msg = {'r': result}
        else:
            msg = {'e': encodeException(exc)}
        try:
            # serialization errors can occur here.
            self.send(reply_node, reply_addr, msg)
        except SerializationError, exc:
            self.send(reply_node, reply_addr, {'e': encodeException(exc)})

    def send(self, node, addr, msg, errh=None):
        msg['o'] = addr
        pcol = self._peer_protocol(node)
        if pcol == 'json':
            if self.verbose:
                print getattr(self.node, 'client_ip', ''), 'Out', msg
            enc = JSON_CODEC.encode(msg, self.json_ctx)
        elif pcol == 'local':
            enc = rmap(self.delocalize, msg)
        else:
            enc = encodes(msg, self.remote_ctx)
        self.node.send(node, enc, errh=errh)

    def provide(self, addr, obj):
        self.storage[addr] = obj
        return Proxy(self.node_id, addr, self)

    def provideAll(self, d):
        for addr, obj in d.iteritems():
            self.provide(addr, obj)

    def call(self, node, addr, method, args):
        cb = self.thread_model.makeCallback()
        reply_addr = '@' + self.vat_id + '/' + randomString()
        self.callbacks[reply_addr] = cb
        msg = {'m': method,
               'a': args,
               'O': reply_addr}
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

    def sendToName(self, name, msg):
        try:
            getn = self.storage.resources['#env'].ns.getn
        except AttributeError, KeyError:
            return
        self.lput(getn(name)._path, msg)

    def _notifyNodeObserver(self, ev, node_id):
        msg = {'m': ev, 'a': (node_id,)}
        self.sendToName('node_observer', msg)
