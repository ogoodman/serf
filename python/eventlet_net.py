"""Net object using eventlet."""

import eventlet
import struct
import threading
import traceback
from eventlet.green import socket, ssl
from eventlet.timeout import Timeout
from eventlet.event import Event
from eventlet import greenthread
from lib.publisher import Publisher

DEFAULT_PORT = 6502

MSG = 0
NODE_NAME = 1
CLOSE = 2

SSL_OPTS = ['keyfile', 'certfile', 'cert_reqs', 'ssl_version', 'ca_certs']

def getAddr(node):
    parts = node.split(':', 1)
    if len(parts) == 2:
        host, port = parts[0], int(parts[1])
    else:
        host, port = node, DEFAULT_PORT
    return host, port

class Net(Publisher):
    def __init__(self, node_id, verbose=False, **kw):
        Publisher.__init__(self)
        self.node_id = node_id
        self.nodes = {}
        self.loop_in = None
        self.cond = threading.Condition()
        self.todo = []
        self.wait_for_close = []
        self.loop = None
        self.lsock = None
        self.thread = threading.currentThread()
        self.verbose = verbose
        self.ssl = kw.get('use_ssl', False)
        self.ssl_kw = dict([(k, v) for k, v in kw.items() if k in SSL_OPTS])
        
    def processWrap(self, socket, address):
        if self.ssl:
            socket = ssl.wrap_socket(socket, server_side=True, **self.ssl_kw)
        self.process(socket, address)

    def process(self, sock, address, node=None):
        if self.verbose:
            print self.node_id, 'connection from %s:%s' % address
        while True:
            header = sock.recv(5)
            if len(header) < 5:
                if self.verbose:
                    print self.node_id, '%s %s disconnected' % (node, address)
                break
            what, msg_len = struct.unpack('>bI', header)
            if msg_len:
                msg = sock.recv(msg_len)
            else:
                msg = ''
            if len(msg) < msg_len:
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
        if node in self.nodes:
            del self.nodes[node]
        if not self.nodes:
            self._nobodyConnected()
            
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
        if threading.currentThread() != self.thread:
            return self.callFromThread(self.send, node, msg, errh)
        try:
            self._send(node, msg)
        except Exception, e:
            # self.notify('error', e)
            if errh is not None:
                errh(e)
            else:
                traceback.print_exc()

    def _send(self, node, msg):
        if node not in self.nodes:
            address = getAddr(node)
            sock = eventlet.connect(address)
            if self.ssl:
                sock = ssl.wrap_socket(sock)
            sock.send(struct.pack('>bI', NODE_NAME, len(self.node_id)))
            sock.send(self.node_id)
            self.nodes[node] = sock
            self.notify('connected', node)
            eventlet.spawn(self.process, sock, address, node)
        else:
            sock = self.nodes[node]
        sock.send(struct.pack('>bI', MSG, len(msg)))
        sock.send(msg)

    def sendDisconnect(self, node):
        self.nodes[node].send(struct.pack('>bI', CLOSE, 0))

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
            self.loop = eventlet.spawn(eventlet.serve, self.lsock, self.processWrap)

    def serve(self, noblock=True):
        self.startLoopback()
        self.listen()
        try:
            eventlet.serve(self.lsock, self.processWrap)
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
