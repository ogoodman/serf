#!/usr/bin/python

"""Demo of websockets. 

TODO: reimplement using pure eventlet websocket module.
"""

import eventlet
import weakref
from serf.eventlet_thread import EventletThread
from serf.websocket_handler import WebSocketHandler, CURRENT
from serf.bound_method import BoundMethod
from serf.rpc_handler import RPCHandler

from serf.transport import Transport
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

transport = Transport(SERF_NODE)
objects = {
    'table': TABLE,
}

rpc = RPCHandler(transport, objects, thread)
rpc.safe.append('serf.tables')

def handle(socket, client_address):
    print client_address, 'connected'
    transport = WebSocketHandler(socket, client_address)
    thread = EventletThread()
    thread.callFromThread = thread.call
    handler = RPCHandler(transport, {}, t_model=thread, verbose=True)
    handler.provide('table', TH_TABLE)
    transport.handle()
    return handler

if __name__ == '__main__':
    server = eventlet.listen(('0.0.0.0', 9900))
    pool = eventlet.GreenPool(10000)
    try:
        thread.start()
        print 'Serf Server 0.1', SERF_NODE
        pool.spawn_n(transport.serve)
        while True:
            new_sock, address = server.accept()
            pool.spawn_n(handle, new_sock, address)
    except KeyboardInterrupt:
        for conn in CURRENT.items():
            conn.send('browser', '', code=0x88) # send CLOSE.
        thread.stop()
        print '\nBye'
