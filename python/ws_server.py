"""Simple Object RPC service.

TODO: reimplement using pure eventlet websocket module.
"""

import eventlet
import weakref
import types
from serf.eventlet_thread import EventletThread
from serf.ws_transport import WSTransport
from serf.rpc_handler import RPCHandler

class FuncAdapter(object):
    def __init__(self, func):
        self.func = func
    def initSession(self, handler):
        self.func(handler)
    def closeSession(self, handler):
        pass

def serve_ws(factory, port, verbose=False, jc_opts=None):
    if type(factory) is types.FunctionType:
        factory = FuncAdapter(factory)
    def handler(transport):
        # transport is a ws_transport.WebSocketHandler
        thread = EventletThread()
        thread.callFromThread = thread.call
        handler = RPCHandler(transport, {}, t_model=thread, verbose=verbose, jc_opts=jc_opts)
        handler.client_address = (transport.client_ip, transport.client_address[1])
        hproxy = weakref.proxy(handler)
        factory.initSession(hproxy)
        try:
            transport.handle()
        except:
            pass
        factory.closeSession(hproxy)
    transport = WSTransport(port, handler=handler)
    transport.serve()
