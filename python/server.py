#!/usr/bin/python

"""Server for distributed capabilities."""

import os
from serf.transport import Transport
from serf.fs_dict import FSDict
from serf.eventlet_thread import EventletThread
from serf.storage import Storage
from serf.vat import Vat
from serf.util import codeDir

if __name__ == '__main__':
    NODE = '127.0.0.1:6502'
    store = FSDict(os.path.join(codeDir(), 'data/server'))

    SSL = {
        'certfile': os.path.join(codeDir(), 'data/host.cert'),
        'keyfile': os.path.join(codeDir(), 'data/host.key')
    }

    net = Transport(NODE, ssl=SSL)

    thread = EventletThread()
    storage = Storage(store, t_model=thread)
    vat = Vat(net, storage, t_model=thread)

    thread.start()
    print 'Serf Server 0.1', NODE
    net.serve()
    thread.stop()
