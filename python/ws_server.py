#!/usr/bin/python

import eventlet
import weakref
from serf.eventlet_thread import EventletThread
from serf.websocket_handler import WebSocketHandler, CURRENT
from serf.model import Model
from serf.bound_method import BoundMethod
from serf.vat import Vat

SINGLETON_MODEL = Model()

class SquareCaller(object):
    def __init__(self, vat, oid):
        self.vat = weakref.ref(vat)
        self.oid = oid
    def useSquarer(self, sq, n):
        r = sq.square(n)
        print 'square of %s is %s' % (n, r)
        return r
    def callSquare(self, square, n):
        r = square(n)
        print 'square of %s is %s' % (n, r)
        return r
    def subscribeToClient(self, prx):
        method = BoundMethod(self.vat(), self.oid, 'onClientEvent', 'server')
        prx.subscribe('event', method)
    def onClientEvent(self, ev, info):
        print 'got event', ev, info

def handle(socket, client_address):
    print client_address, 'connected'
    transport = WebSocketHandler(socket, client_address)
    thread = EventletThread()
    thread.callFromThread = thread.call
    handler = Vat('server', '', {}, transport, t_model=thread, verbose=True)
    handler.provide('shared', SINGLETON_MODEL)
    handler.provide('private', Model())
    handler.provide('sqcaller', SquareCaller(handler, 'sqcaller'))
    transport.handle()
    return handler

if __name__ == '__main__':
    server = eventlet.listen(('0.0.0.0', 9999))
    pool = eventlet.GreenPool(10000)
    try:
        while True:
            new_sock, address = server.accept()
            pool.spawn_n(handle, new_sock, address)
    except KeyboardInterrupt:
        for conn in CURRENT.items():
            conn.send('browser', '', code=0x88) # send CLOSE.
        print '\nBye'
