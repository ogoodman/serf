#!/usr/bin/python

"""Demo of implementing a back-end using RPC over a web-socket."""

import eventlet
from serf.eventlet_thread import EventletThread
from serf.rpc_handler import RPCHandler
from serf.transport import Transport
from serf.ws_transport import WSTransport
from serf.fs_dict import FSDict
from serf.storage import Storage

from serf.tables.table import *
from serf.tables.query import *
from serf.tables.table_handle import TableHandle

SERF_NODE = '127.0.0.1:6506'

thread = EventletThread()

store = FSDict('/var/lib/serf/tables')
storage = Storage(store, t_model=thread)

if 'table' not in storage:
    storage['table'] = Table()
TABLE = storage['table']
TH_TABLE = TableHandle(TABLE)

JC_OPTS = dict(hooks=JC_HOOKS, safe=['serf.tables'], auto_proxy=True)

def handle(transport):
    thread = EventletThread()
    thread.callFromThread = thread.call
    handler = RPCHandler(transport, {}, t_model=thread, jc_opts=JC_OPTS)
    handler.provide('table', TH_TABLE)
    transport.handle()

if __name__ == '__main__':
    print 'Table Server', SERF_NODE

    transport = Transport(SERF_NODE)
    rpc = RPCHandler(transport, storage, thread)
    rpc.safe.append('serf.tables')
    thread.start()
    eventlet.spawn_n(transport.serve)

    ws_transport = WSTransport(9900, handler=handle)
    ws_transport.serve()

    thread.stop()
    print '\nBye'
