"""Transport object using eventlet."""

import eventlet
import struct
import threading
import traceback
from eventlet.green import socket, ssl
from eventlet.timeout import Timeout
from eventlet.event import Event
from eventlet import greenthread
from serf.publisher import Publisher

DEFAULT_PORT = 6502

DISCONNECTED = -1
MSG = 0
NODE_NAME = 1
CLOSE = 2
SSL_OPTIONS = 3
SSL_CHOICE = 4

SSL_OPTS = ['keyfile', 'certfile', 'cert_reqs', 'ssl_version', 'ca_certs']

# The SSL/plain handshake. On connection the server sends the client
# a list of supported options. The client sends back an SSL choice
# choosing one of the options. If the choice is SSL, both ends then
# upgrade to SSL before continuing.

def getAddr(node):
    parts = node.split(':', 1)
    if len(parts) == 2:
        host, port = parts[0], int(parts[1])
    else:
        host, port = node, DEFAULT_PORT
    return host, port

class Transport(Publisher):
    """Implements Transport. Connector for serf protocol."""
    def __init__(self, node_id, verbose=False, ssl=None):
        Publisher.__init__(self)
        self.node_id = node_id
        self.path = ''
        self.nodes = {}
        self.loop_in = None
        self.cond = threading.Condition()
        self.todo = []
        self.wait_for_close = []
        self.loop = None
        self.lsock = None
        self.thread = threading.currentThread()
        self.verbose = verbose
        self.ssl = ssl

    def readall(self, socket, n):
        """Defragment and read n bytes."""
        buf = []
        count = 0
        while count < n:
            data = socket.recv(min(n - count, 4096))
            if not data:
                return ''
            buf.append(data)
            count += len(data)
        return ''.join(buf)

    def read(self, socket):
        """Receive a single control-byte, message pair."""
        header = self.readall(socket, 5)
        if len(header) < 5:
            return DISCONNECTED, ''
        what, msg_len = struct.unpack('>bI', header)
        if msg_len > 0:
            msg = self.readall(socket, msg_len)
        else:
            msg = ''
        if len(msg) < msg_len:
            return DISCONNECTED, ''
        return what, msg

    def write(self, socket, what, msg):
        """Write a single control-byte and message."""
        socket.sendall(struct.pack('>bI', what, len(msg)))
        if msg:
            socket.sendall(msg)
        
    def accept(self, socket, address):
        """Called when listening with new client connections."""

        # This could be made more flexible but that is an implementation
        # detail of the server and does not affect the protocol.
        ssl_opts = 'SP' if self.ssl else 'P'

        self.write(socket, SSL_OPTIONS, ssl_opts)
        what, choice = self.read(socket)
        if what == DISCONNECTED:
            return
        if what != SSL_CHOICE or len(choice) != 1 or (choice not in ssl_opts):
            if self.verbose:
                print 'invalid response to SSL_OPTIONS from', address
            return
        if choice == 'S':
            socket = ssl.wrap_socket(socket, server_side=True, **self.ssl)
        self.process(socket, address)

    def process(self, sock, address, node=None):
        """Handler for all established connections.

        This processes all incoming messages, including the node-name
        part of the handshake.
        """
        if self.verbose:
            print self.node_id, 'connection from %s:%s' % address
        while True:
            what, msg = self.read(sock)
            if what == DISCONNECTED:
                if self.verbose:
                    print self.node_id, '%s %s disconnected' % (node, address)
                break
            if what == NODE_NAME:
                node = msg
                if node in self.nodes:
                    if self.verbose:
                        print self.node_id, '%s %s already connected' % (node, address)
                else:
                    if self.verbose:
                        print self.node_id, '%s %s connected' % (node, address)
                    self.nodes[node] = sock
                    self.notify('connected', node)
            elif what == MSG:
                self.notify('message', {'from': node, 'pcol': 'serf', 'message': msg})
            elif what == CLOSE:
                if self.verbose:
                    print self.node_id, '%s %s requested close' % (node, address)
                break
        self.closeConnection(node)
            
    def _nobodyConnected(self):
        el = self.wait_for_close
        self.wait_for_close = []
        for e in el:
            e.send()

    def waitForNobodyConnected(self):
        if not self.nodes:
            return
        ev = Event()
        self.wait_for_close.append(ev)
        ev.wait()

    def callFromThread(self, *args):
        with self.cond:
            self.todo.append(args)
        self.loop_in.send('\x01')

    def doCalls(self, loop_out):
        while loop_out.recv(1):
            with self.cond:
                todo = self.todo
                self.todo = []
            for args in todo:
                try:
                    args[0](*args[1:])
                except:
                    traceback.print_exc()
        loop_out.close()
        self.loop_in.close()

    def doStop(self):
        raise eventlet.StopServe()

    def send(self, node, msg, pcol='serf', errh=None):
        """Send a message to a node."""
        if threading.currentThread() != self.thread:
            return self.callFromThread(self.send, node, msg, pcol, errh)
        try:
            if node not in self.nodes:
                sock = self.connect(node)
            else:
                sock = self.nodes[node]
            self.write(sock, MSG, msg)
        except Exception, e:
            if errh is not None:
                errh(e)
            else:
                traceback.print_exc()

    def connect(self, node):
        """Connect with a new node."""
        address = getAddr(node)
        sock = eventlet.connect(address)
        what, ssl_opts = self.read(sock)
        if what != SSL_OPTIONS or (
            'S' not in ssl_opts and 'P' not in ssl_opts):
            raise Exception('%s gave no acceptable SSL options' % node)
        # We could make this more flexible, having preferences based
        # on the IP range of the server etc.
        if 'S' in ssl_opts:
            self.write(sock, SSL_CHOICE, 'S')
            sock = ssl.wrap_socket(sock)
        else:
            self.write(sock, SSL_CHOICE, 'P')
        self.write(sock, NODE_NAME, self.node_id)
        self.nodes[node] = sock
        self.notify('connected', node)
        eventlet.spawn(self.process, sock, address, node)
        return sock

    def sendDisconnect(self, node):
        self.nodes[node].sendall(struct.pack('>bI', CLOSE, 0))

    def closeConnection(self, node):
        if node in self.nodes:
            sock = self.nodes.pop(node)
            sock.close()
        if not self.nodes:
            self._nobodyConnected()

    def startLoopback(self):
        self.loop_in, loop_out = socket.socketpair()
        eventlet.spawn(self.doCalls, loop_out)
        self.thread = threading.currentThread()

    def listen(self):
        addr = getAddr(self.node_id)
        self.lsock = eventlet.listen(addr)
        self.notify('online', self.node_id)

    def start(self):
        self.startLoopback()
        if self.lsock is not None:
            self.loop = eventlet.spawn(eventlet.serve, self.lsock, self.accept)

    def serve(self, noblock=True):
        self.startLoopback()
        self.listen()
        try:
            eventlet.serve(self.lsock, self.accept)
        except KeyboardInterrupt:
            pass

    def stop(self):
        for node in list(self.nodes):
            self.sendDisconnect(node)
        with Timeout(.5, False):
            self.waitForNobodyConnected()
        if self.lsock is not None:
            self.lsock.close()
            self.lsock = None
        for node in list(self.nodes):
            self.closeConnection(node)
        if self.loop is not None:
            self.loop.kill(eventlet.StopServe())
