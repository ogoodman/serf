#!/usr/bin/python

"""Demo of implementing a back-end using RPC over a web-socket."""

import sys
import eventlet
from serf.eventlet_thread import EventletThread
from serf.rpc_handler import RPCHandler
from serf.transport import Transport
from serf.ws_transport import WSTransport
from serf.fs_dict import FSDict
from serf.storage import Storage

from serf.user.login import Login
from serf.user.admin import Admin
from serf.tables.table import JC_HOOKS

ROOT_DIR = sys.argv[1]

SERF_NODE = '127.0.0.1:6508'

thread = EventletThread()

store = FSDict(ROOT_DIR)
storage = Storage(store, t_model=thread)

if 'login' not in storage:
    storage['login'] = Login(storage)
if 'admin' not in storage:
    storage['admin'] = Admin(storage)
LOGIN = storage['login']

JC_OPTS = dict(hooks={}, auto_proxy=True)

def handle(transport):
    thread = EventletThread()
    thread.callFromThread = thread.call
    handler = RPCHandler(transport, {}, t_model=thread, jc_opts=JC_OPTS)
    handler.provide('login', LOGIN)
    transport.handle()

if __name__ == '__main__':
    print 'Cap Server', SERF_NODE

    transport = Transport(SERF_NODE)
    rpc = RPCHandler(transport, storage, thread, verbose=True)
    rpc.safe.append('serf.tables')
    thread.start()
    eventlet.spawn_n(transport.serve)

    ws_transport = WSTransport(9902, handler=handle)
    ws_transport.serve()

    thread.stop()
    print '\nBye'
