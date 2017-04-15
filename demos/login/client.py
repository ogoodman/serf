#!/usr/bin/env python

"""Handy stuff for the command line."""

from serf.rpc_handler import RPCHandler
from serf.transport import Transport
from serf.eventlet_thread import EventletThread
from serf.proxy import Proxy
from serf.repl_proxy import REPLProxy

SERVER = '127.0.0.1:6508'

net = Transport()

thread = EventletThread()
rpc = RPCHandler(net, {}, t_model=thread)
rpc.safe.append('serf.tables.table_handle')

def remote(x):
    return REPLProxy(rpc.makeProxy(x, SERVER), thread)

thread.start(True)

thread.callFromThread(net.start)

admin = remote('admin')
