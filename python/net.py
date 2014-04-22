"""TCP transport for a Node."""

import struct
import traceback
import threading
from serf.worker import Worker
from serf.net_base import BaseReceiver, NetBase
from lib.publisher import Publisher

DEFAULT_PORT = 6502

UINT_MAX = 2**32-1

MSG = 0
NODE_NAME = 1
CLOSE = 2

# ISSUE: we're allowing clients to tell the server their node id.
# While there isn't much advantage for a client to send an incorrect
# node id, the current version of the code allows it to deny service
# to the true owner of that node.

class Receiver(BaseReceiver):
    def __init__(self, sock, addr, net, w_ok=True):
        BaseReceiver.__init__(self, sock, addr, net, w_ok)
        self.node = None
        self.want = None
        self.what = None

    def onRead(self):
        # we're either getting size data or message data
        while True:
            if self.want is None:
                if self.size < 5:
                    break
                header = self.get(5)
                self.what, self.want = struct.unpack('>bI', header)
            else:
                if self.size < self.want:
                    break
                msg = self.get(self.want)
                self.want = None
                self.handle(msg)

    def handle(self, msg):
        if self.what == NODE_NAME:
            self.node = msg
            if self.node not in self.net.nodes:
                if self.net.verbose:
                    print 'adding client', self.node
                self.net.connected(self)
            else:
                if self.net.verbose:
                    print 'already connected:', self.node
        elif self.what == MSG:
            self.net.notify('message', {'from': '', 'pcol': 'serf', 'message': msg})
        elif self.what == CLOSE:
            if self.net.verbose:
                print 'disconnect request from', self.node
            self.net.closeConnection(self.node)
        else:
            if self.net.verbose:
                print 'unexpected message type', self.what

    def sendNodeName(self, node, errh=None):
        self.send(struct.pack('>bI', NODE_NAME, len(node)), errh)
        self.send(node, errh)

    def sendMsg(self, msg, errh=None):
        self.send(struct.pack('>bI', MSG, len(msg)), errh)
        self.send(msg, errh)

    def sendClose(self):
        self.send(struct.pack('>bI', CLOSE, 0))

class NetCore(NetBase, Publisher):
    def __init__(self, node, verbose=False, **kw):
        # The node_id is used to determine which ip/port to listen on
        # and the node_id to send when connecting with a peer.
        NetBase.__init__(self, verbose, **kw)
        Publisher.__init__(self)
        self.node = node
        self.nodes = {}

    def getAddr(self, node):
        parts = node.split(':', 1)
        if len(parts) == 2:
            host, port = parts[0], int(parts[1])
        else:
            host, port = node, DEFAULT_PORT
        return host, port

    def makeReceiver(self, conn, addr, w_ok=True):
        return Receiver(conn, addr, self, w_ok)

    def connected(self, receiver):
        self.nodes[receiver.node] = receiver.fileno()
        self.notify('connected', receiver.node)
        
    def disconnected(self, receiver):
        node = receiver.node
        if node is not None:
            # Check because of 'already connected' case in
            # Receiver.handle() above.
            if self.nodes.get(node) == receiver.fileno():
                if self.verbose:
                    print 'removing client', node
                del self.nodes[node]
        if self.verbose:
            print 'disconnected', receiver.addr

    def listen(self): # core
        addr = self.getAddr(self.node)
        NetBase.listen(self, addr)
        self.notify('online', self.node)

    def onShutdown(self):
        self.shutdown(0.5)
        if self.verbose:
            print 'sending disconnect to %d peer(s)' % len(self.incoming)
        for receiver in self.incoming.values():
            receiver.sendClose()

    def cleanup(self):
        NetBase.cleanup(self)
        self.nodes = {}

    def send(self, node, msg, errh=None):
        # node is <host-or-ip>[:<port>]
        # If running, do it in the main loop.
        assert(len(msg) <= UINT_MAX)
        if node not in self.nodes:
            addr = self.getAddr(node)
            receiver = self.connect(addr, errh)
            if receiver is None:
                return
            receiver.node = node
            self.nodes[node] = receiver.fileno()
            # Tell remote server who we are.
            receiver.sendNodeName(self.node, errh)
        else:
            fileno = self.nodes[node]
            receiver = self.incoming[fileno]
        receiver.sendMsg(msg, errh)

    def closeConnection(self, node):
        fileno = self.nodes.pop(node)
        self.close(fileno)

class Net(Worker):
    def __init__(self, node, verbose=False, **kw):
        Worker.__init__(self, NetCore(node, verbose, **kw))

    def listen(self):
        self.callTS(self.scheduler.listen)

    def closeConnection(self, node):
        self.callTS(self.scheduler.closeConnection, node)

    def send(self, node, msg, errh=None):
        self.callTS(self.scheduler.send, node, msg, errh)

    def serve(self):
        # Blocks until shudown.
        assert(self.thread is None)
        self.scheduler.listen()
        self.scheduler.start()
        self.run()

    def subscribe(self, event, cb):
        self.scheduler.subscribe(event, cb)

    def unsubscribe(self, event, cb):
        self.scheduler.unsubscribe(event, cb)
