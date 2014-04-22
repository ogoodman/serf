#!/usr/bin/python

"""Server for distributed capabilities."""

import os
from serf.eventlet_net import Net
from serf.fs_dict import FSDict
from serf.eventlet_thread import EventletThread
from serf.node import Node
from serf.storage import Storage
from serf.vat import Vat
from serf.util import codeDir

if __name__ == '__main__':
    NODE = '127.0.0.1:6502'
    store = FSDict(os.path.join(codeDir(), 'data/server'))

    CERT = os.path.join(codeDir(), 'data/host.cert')
    KEY = os.path.join(codeDir(), 'data/host.key')

    net = Net(NODE, use_ssl=True, keyfile=KEY, certfile=CERT)
    node = Node(NODE, net, store)

    thread = EventletThread()
    storage = Storage(store, t_model=thread)
    vat = Vat(NODE, '0', storage, t_model=thread)
    node.addVat(vat)

    thread.start()
    print 'Serf Server 0.1', NODE
    net.serve()
    thread.stop()
