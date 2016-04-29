#!/usr/bin/env python

"""Handy stuff for the command line."""

import os
import sys
import time

from serf.rpc_handler import RPCHandler
from serf.transport import Transport
from serf.eventlet_thread import EventletThread
from serf.proxy import Proxy
from serf.repl_proxy import REPLProxy
from serf.po.printer import Printer

SERVER = '127.0.0.1:6506'

def lfunc(a):
    print 'func(%r)' % a

def subscriber(ev, info):
    print 'event:', ev, info

transport = Transport()
objects = {
    'printer': Printer(),
    'func': lfunc,
    'subscriber': subscriber,
}
thread = EventletThread()
rpc = RPCHandler(transport, objects, t_model=thread)
rpc.safe.append('serf.po')

def wrap(x):
    return REPLProxy(x, thread)

# thread.start(True) means start a new thread.
thread.start(True)
thread.callFromThread(transport.start)

table = wrap(Proxy(SERVER, 'table', rpc))
printer = wrap(Proxy(SERVER, 'printer', rpc))
caller = wrap(Proxy(SERVER, 'proxy_caller', rpc))
func = wrap(Proxy(SERVER, 'func', rpc))

proxy = rpc.makeProxy('printer')
sub = rpc.makeProxy('subscriber')
lfun = rpc.makeProxy('func')
