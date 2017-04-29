#!/usr/bin/python

"""Server for distributed capabilities."""

import os
import sys
from serf.transport import Transport
from serf.fs_dict import FSDict
from serf.eventlet_thread import EventletThread
from serf.storage import Storage
from serf.rpc_handler import RPCHandler
from serf.util import codeDir, dataRoot

if __name__ == '__main__':
    NODE = '127.0.0.1:6502'
    DATA_ROOT = os.path.join(dataRoot(), 'server')
    store = FSDict(DATA_ROOT)

    SSL = {
        'certfile': os.path.join(codeDir(), 'data/host.cert'),
        'keyfile': os.path.join(codeDir(), 'data/host.key')
    }

    net = Transport(NODE, ssl=SSL, verbose=('-v' in sys.argv))

    thread = EventletThread()
    storage = Storage(store)
    vat = RPCHandler(net, storage, t_model=thread)

    thread.start()
    print 'Serf Server 0.1', NODE
    print 'data-root =', DATA_ROOT
    net.serve()
    thread.stop()
    print '\rBye'
