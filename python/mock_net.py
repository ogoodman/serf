"""Mock internet."""

import socket
from serf.node import Node
from serf.vat import Vat
from serf.storage import Storage
from lib.publisher import Publisher

class MockEndpoint(Publisher):
    def send(self, node, msg, errh=None):
        self.notify('send', [node, msg, errh])

class MockNet(object):
    def __init__(self):
        self.end = {}
        self.node = {}
        self.offline = set()

    def send(self, node, msg, errh=None):
        if node in self.offline:
            errh(socket.error())
            return
        try:
            self.end[node].notify('message', {'node': '', 'message':msg})
        except Exception, e:
            if errh is not None:
                errh(e)

    def send0(self, ev, info):
        self.send(*info)

    def addNode(self, node):
        if node not in self.end:
            self.end[node] = MockEndpoint()
            self.end[node].subscribe('send', self.send0)
        return self.end[node]

    def addVat(self, node_id, vat_id, store, t_model=None):
        storage = Storage(store, t_model=t_model)
        vat = Vat(node_id, vat_id, storage, t_model=t_model)
        if node_id not in self.node:
            transport = self.addNode(node_id)
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
