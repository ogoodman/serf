"""Mock internet."""

import socket
import weakref
from serf.rpc_handler import RPCHandler
from serf.storage import Storage
from serf.publisher import Publisher

class MockTransport(Publisher):
    """Implements Transport. For use in tests."""
    def __init__(self, node_id, net=None):
        Publisher.__init__(self)
        self.net = weakref.ref(net) if net is not None else None
        self.node_id = node_id
        self.path = ''

    def send(self, node, msg, errh=None):
        self.net().send(node, msg, self.node_id, errh=errh)

class MockNet(object):
    def __init__(self):
        self.end = {}
        self.offline = set()

    def send(self, node, msg, from_, errh=None):
        if node in self.offline:
            errh(socket.error())
            return
        try:
            self.end[node].notify('message', {'from':from_, 'message': msg})
        except Exception, e:
            if errh is not None:
                errh(e)

    def addNode(self, node):
        if node not in self.end:
            self.end[node] = MockTransport(node, self)
        return self.end[node]

    def addRPCHandler(self, node_id, vat_id, store, t_model=None):
        transport = self.addNode(node_id)
        storage = Storage(store, t_model=t_model)
        vat = RPCHandler(transport, storage, t_model=t_model)
        return storage, vat

    def goOffline(self, node):
        self.offline.add(node)

    def goOnline(self, node):
        self.offline.discard(node)
        nn = self.end[node]
        for k, n in self.end.items():
            if k != node:
                n.notify('connected', node)
                nn.notify('connected', k)
