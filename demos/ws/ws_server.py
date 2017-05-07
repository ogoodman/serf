#!/usr/bin/python

"""Demo of websockets."""

import sys
from serf.ws_server import serve_ws
from serf.model import Model
from serf.bound_method import JCBoundMethod

SINGLETON_MODEL = Model()

class SquareCaller(object):
    def __init__(self, vat, oid):
        self.vat = vat
        self.oid = oid
        self.verbose = '-v' in sys.argv
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
        method = JCBoundMethod(self.vat(), self.oid, 'onClientEvent', 'server')
        prx.subscribe('event', method)
    def onClientEvent(self, ev, info):
        if self.verbose:
            print 'got event', ev, info

class Ping(object):
    def ping(self):
        return 'pong'

def init_session(handler):
    handler.provide('shared', SINGLETON_MODEL)
    handler.provide('private', Model())
    handler.provide('sqcaller', SquareCaller(handler, 'sqcaller'))
    handler.provide('ping', Ping())

if __name__ == '__main__':
    verbose = '-v' in sys.argv
    serve_ws(init_session, 9999, verbose)
    print '\nBye'
