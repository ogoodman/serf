"""Mock internet."""

import socket
from serf.node import Node
from serf.vat import Vat
from serf.storage import Storage
from lib.publisher import Publisher

class MockEndpoint(Publisher):
    def __init__(self, node_id):
        Publisher.__init__(self)
        self.node_id = node_id

    def send(self, node, msg, errh=None):
        self.notify('send', [node, msg, errh, self.node_id])

class MockNet(object):
    def __init__(self):
        self.end = {}
        self.node = {}
        self.offline = set()

    def send(self, node, msg, errh=None, frm=''):
        if node in self.offline:
            errh(socket.error())
            return
        try:
            self.end[node].notify('message', {'from': frm, 'pcol': 'serf', 'message': msg})
        except Exception, e:
            if errh is not None:
                errh(e)

    def send0(self, ev, info):
        self.send(*info)

    def addNode(self, node):
        if node not in self.end:
            self.end[node] = MockEndpoint(node)
            self.end[node].subscribe('send', self.send0)
        return self.end[node]

    def addVat(self, node_id, vat_id, store, t_model=None):
        assert(node_id not in self.end)
        transport = self.addNode(node_id)
        storage = Storage(store, t_model=t_model)
        vat = Vat(node_id, vat_id, storage, t_model=t_model)
        self.node[node_id] = Node(node_id, transport, {})
        self.node[node_id].addVat(vat)
        return storage, vat

    def goOffline(self, node):
        self.offline.add(node)

    def goOnline(self, node):
        self.offline.discard(node)
        if node not in self.end:
            return
        nn = self.end[node]
        for k, n in self.end.items():
            if k != node:
                n.notify('connected', node)
                nn.notify('connected', k)
