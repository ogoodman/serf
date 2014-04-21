"""Endpoint for a set of Vats."""

import threading
from cStringIO import StringIO
from serialize import decode


class Node(object):
    def __init__(self, node_id, net, store):
        self.node_id = node_id
        self.net = net
        self.store = store
        self.vats = {}
        self.vat_id = {}
        self.default_vat_id = None
        self.lock = threading.Lock()
        net.subscribe('message', self.handle)
        net.subscribe('online', self.online)
        net.subscribe('connected', self.connected)

    def addVat(self, vat):
        self.vats[vat.vat_id] = vat
        if self.default_vat_id is None:
            self.default_vat_id = vat.vat_id
        vat.setNode(self)
        vat.setVatMap(self)

    def getVatId(self, path):
        if path.startswith('@'):
            return path.split('/', 1)[0][1:]
        with self.lock:
            try:
                return self.vat_id[path]
            except KeyError:
                pass
            try:
                vat_id = self.store['vat_ids/' + path]
            except KeyError:
                vat_id = self.default_vat_id
            self.vat_id[path] = vat_id
            return vat_id

    def setVatId(self, path, vat_id):
        with self.lock:
            if self.vat_id.get(path) != vat_id:
                self.vat_id[path] = vat_id
                if vat_id != self.default_vat_id:
                    self.store['vat_ids/' + path] = vat_id

    def delVatId(self, path):
        with self.lock:
            try:
                del self.vat_id[path]
            except KeyError:
                pass
            try:
                del self.store['vat_ids/' + path]
            except KeyError:
                pass

    def handle(self, ev, msg):
        """Peeks at address to find which vat to deliver it to."""
        f = StringIO(msg['message'])
        addr = decode(f) # msg is addr, body
        vat_id = self.getVatId(addr)
        self.vats[vat_id].handle('message', msg)

    def send(self, node, msg, errh=None):
        if node == self.node_id:
            addr = msg['o']
            vat_id = self.getVatId(addr)
            self.vats[vat_id].lput(addr, msg)
        else:
            self.net.send(node, msg, errh=errh)

    def sendToName(self, name, msg):
        # The name must be a name owned by the default vat.
        vat = self.vats[self.default_vat_id]
        ref = vat.storage.getn(name)
        vat.lput(ref._path, msg)

    def online(self, ev, node_id):
        msg = {'m': 'online', 'a': (node_id,)}
        self.sendToName('node_observer', msg)

    def connected(self, ev, node_id):
        msg = {'m': 'connected', 'a': (node_id,)}
        self.sendToName('node_observer', msg)

    def subscribe(self, event, cb):
        pass
