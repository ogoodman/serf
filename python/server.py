#!/usr/bin/python

"""Server for distributed capabilities."""

import os
from fred.eventlet_net import Net
from fred.fs_dict import FSDict
from fred.eventlet_thread import EventletThread
from fred.node import Node
from fred.storage import Storage
from fred.vat import Vat
from fred.util import codeDir

if __name__ == '__main__':
    NODE = '127.0.0.1:6502'
    store = FSDict(os.path.join(codeDir(), 'data/server'))

    CERT = os.path.join(codeDir(), 'data/host.cert')
    KEY = os.path.join(codeDir(), 'data/host.key')

    net = Net(NODE, use_ssl=True, keyfile=KEY, certfile=CERT)
    node = Node(NODE, net, store)

    thread = EventletThread()
    storage = Storage(store, '0', node, t_model=thread)
    vat = Vat(NODE, '0', storage, t_model=thread)
    storage.rpc = vat
    node.addVat(vat)

    thread.start()
    print 'Fred Server 0.1', NODE
    net.serve()
    thread.stop()
