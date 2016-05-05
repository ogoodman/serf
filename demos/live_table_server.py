#!/usr/bin/python

"""Demo of websockets. 

TODO: reimplement using pure eventlet websocket module.
"""

import eventlet
from serf.eventlet_thread import EventletThread
from serf.rpc_handler import RPCHandler
from serf.transport import Transport
from serf.ws_transport import WSTransport
from serf.tables.table import *
from serf.tables.query import *
from serf.tables.table_handle import TableHandle
from serf.fs_dict import FSDict
from serf.storage import Storage
from serf.json_codec import JSON_CODEC

SERF_NODE = '127.0.0.1:6506'

thread = EventletThread()

store = FSDict('tables')
storage = Storage(store, t_model=thread)

if 'table' not in storage:
    storage['table'] = Table()
TABLE = storage['table']
TH_TABLE = TableHandle(TABLE)

JSON_CODEC.hooks['PKey'] = lambda _,args: PKey(*args)
JSON_CODEC.hooks['FieldValue'] = lambda _,args: FieldValue(*args)
JSON_CODEC.hooks['QTerm'] = lambda _,args: QTerm(*args)

def handle(transport):
    thread = EventletThread()
    thread.callFromThread = thread.call
    handler = RPCHandler(transport, {}, t_model=thread, verbose=True)
    handler.provide('table', TH_TABLE)
    transport.handle()

if __name__ == '__main__':
    print 'Table Server', SERF_NODE

    transport = Transport(SERF_NODE)
    objects = {'table': TABLE}
    rpc = RPCHandler(transport, objects, thread)
    rpc.safe.append('serf.tables')
    thread.start()
    eventlet.spawn_n(transport.serve)

    ws_transport = WSTransport(9900, handler=handle)
    ws_transport.serve()

    thread.stop()
    print '\nBye'
