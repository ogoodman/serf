#!/usr/bin/python

"""Demo of websockets. 

TODO: reimplement using pure eventlet websocket module.
"""

import eventlet
import sys
import weakref
from serf.eventlet_thread import EventletThread
from serf.ws_transport import WSTransport
from serf.model import Model
from serf.bound_method import BoundMethod
from serf.rpc_handler import RPCHandler

SINGLETON_MODEL = Model()

class SquareCaller(object):
    def __init__(self, vat, oid, verbose=False):
        self.vat = weakref.ref(vat)
        self.oid = oid
        self.verbose = verbose
    def useSquarer(self, sq, n):
        r = sq.square(n)
        if self.verbose:
            print 'square of %s is %s' % (n, r)
        return r
    def callSquare(self, square, n):
        r = square(n)
        if self.verbose:
            print 'square of %s is %s' % (n, r)
        return r
    def subscribeToClient(self, prx):
        method = BoundMethod(self.vat(), self.oid, 'onClientEvent', 'server')
        prx.subscribe('event', method)
    def onClientEvent(self, ev, info):
        if self.verbose:
            print 'got event', ev, info

class Ping(object):
    def ping(self):
        return 'pong'

def handle(transport):
    verbose = '-v' in sys.argv
    thread = EventletThread()
    thread.callFromThread = thread.call
    handler = RPCHandler(transport, {}, t_model=thread, verbose=verbose)
    handler.provide('shared', SINGLETON_MODEL)
    handler.provide('private', Model())
    handler.provide('sqcaller', SquareCaller(handler, 'sqcaller', verbose))
    handler.provide('ping', Ping())
    transport.handle()

if __name__ == '__main__':
    transport = WSTransport(9999, handler=handle)
    transport.serve()
    print '\nBye'
