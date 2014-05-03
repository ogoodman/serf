"""Monitors the online status of other nodes.

Peers are nodes that want to know when we go online: we ping them
so as to make a connection with them.

When we want to know if a particular node is online, we observe it.
If it is online when we go online, or if it treats us as a peer
when it goes online after us, our observers of that node will get
an online call.
"""

from serf.po.group import Group
import socket

class NodeObserver(object):
    serialize = ('_vat', 'peers', 'observers')

    def __init__(self, vat, peers=None, observers=None):
        self.vat = vat
        self.peers = peers or []
        self.observers = observers or {}
        self.ref = None

    def ping(self, node):
        try:
            self.vat.getRPC().call(node, '', 'ping', ()).wait()
            return True
        except socket.error:
            return False

    def connected(self, node):
        # Called by the Transport transport object.
        if node in self.observers:
            self.observers[node].online(node)

    def online(self, my_node):
        for node in set(self.peers).union(self.observers):
            self.vat.thread_model.call(self.ping, node)

    def addPeer(self, node):
        if node not in self.peers:
            self.peers.append(node)
            self._save()

    def removePeer(self, node):
        try:
            self.peers.remove(node)
        except ValueError:
            pass
        else:
            self._save()

    def addObserver(self, node, obs):
        if node not in self.observers:
            self.observers[node] = Group()
        self.observers[node]._add(obs)
        self._save()

    def removeObserver(self, node, obs):
        if node not in self.observers:
            return
        self.observers[node]._remove(obs)
        if not self.observers[node]:
            del self.observers[node]
        self._save()

    def _save(self):
        pass
