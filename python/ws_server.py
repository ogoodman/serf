#!/usr/bin/python

import eventlet
from serf.eventlet_thread import EventletThread
from serf.websocket_handler import WebSocketHandler, CURRENT
from serf.model import Model
from serf.vat import Vat

SINGLETON_MODEL = Model()

class SquareCaller(object):
    def useSquarer(self, sq, n):
        r = sq.square(n)
        print 'square of %s is %s' % (n, r)
        return r

def handle(socket, client_address):
    print client_address, 'connected'
    transport = WebSocketHandler(socket, client_address)
    thread = EventletThread()
    thread.callFromThread = thread.call
    handler = Vat('server', '', {}, transport, t_model=thread, verbose=True)
    handler.provide('shared', SINGLETON_MODEL)
    handler.provide('private', Model())
    handler.provide('sqcaller', SquareCaller())
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
