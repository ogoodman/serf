#!/usr/bin/python

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

def serve(factory, port, verbose=False):
    if type(factory) is types.FunctionType:
        factory = FuncAdapter(factory)
    def handler(transport):
        thread = EventletThread()
        thread.callFromThread = thread.call
        handler = RPCHandler(transport, {}, t_model=thread, verbose=verbose)
        factory.initSession(weakref.proxy(handler))
        transport.handle()
    transport = WSTransport(port, handler=handler)
    transport.serve()
