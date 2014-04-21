"""Non-blocking TCP peer base."""

import os
import sys
import select
import socket
import ssl
import threading
import errno

SSL_OPTS = ['keyfile', 'certfile', 'cert_reqs', 'ssl_version', 'ca_certs']

class BaseReceiver(object):
    def __init__(self, sock, addr, net, w_ok=True):
        self.size = 0
        self.read = []
        self.sock = sock
        self.addr = addr
        self.net = net
        self.w_ok = w_ok
        self.connected = w_ok
        self.write = []

    def send(self, data, errh=None):
        self.write.append((data, errh))
        if self.w_ok:
            self.doSend()

    def sendError(self, exc):
        # Must call back on all pending sends.
        errhs = set([item[1] for item in self.write])
        for errh in errhs:
            if errh is not None:
                errh(exc)
            else:
                print >>sys.stderr, exc
        self.write = []
        self.net.disconnected(self)
        del self.net.incoming[self.fileno()]

    def doSend(self):
        # We get to here if select said sock was writable.
        if not self.connected:
            err = self.sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
            if err == 0:
                self.connected = True
                if self.net.ssl:
                    self.sock = ssl.wrap_socket(self.sock)
                self.net.connected(self)
            else:
                exc = socket.error(err, os.strerror(err))
                self.sendError(exc)
                return
        while self.write:
            data, errh = self.write[0]
            try:
                self.sock.send(data)
            except socket.error, e:
                err = e.args[0]
                if err in (errno.EAGAIN, errno.EWOULDBLOCK):
                    self.w_ok = False
                else:
                    self.sendError(e)
                return
            del self.write[0] # successfully sent
        self.w_ok = True

    def get(self, n):
        assert(n <= self.size)
        all = ''.join(self.read)
        self.read = [all[n:]]
        self.size -= n
        return all[:n]

    def doRecv(self):
        data = self.sock.recv(4096)
        if data:
            self.read.append(data)
            self.size += len(data)
            self.onRead()
        else:
            if self.sock.fileno() in self.net.incoming:
                del self.net.incoming[self.sock.fileno()]
            self.net.disconnected(self)
            self.sock.close()

    def fileno(self):
        return self.sock.fileno()

    def close(self):
        self.sock.close()

    def onRead(self):
        # Implement me to process received data.
        data = self.get(self.size) # can get up to self.size.

class NetBase(object):
    def __init__(self, verbose=False, **kw):
        self.verbose = verbose
        self.listener = None
        self.loop_in = None
        self.loop_out = None
        self.incoming = {} # socket -> Receiver
        self.timeout = None
        self.todo = []
        self.lock = threading.Lock()
        self.ssl = kw.get('use_ssl', False)
        self.ssl_kw = dict([(k, v) for k, v in kw.items() if k in SSL_OPTS])

    def put(self, args):
        with self.lock:
            self.todo.append(args)
        if self.loop_in is not None:
            self.loop_in.send('\x01')

    def connect(self, addr, errh=None):
        if self.verbose:
            print 'connect', addr
        sock = socket.socket()
        sock.setblocking(0)
        err = sock.connect_ex(addr)
        if err not in (0, errno.EINPROGRESS):
            exc = socket.error(err, os.strerror(err))
            if errh is not None:
                errh(exc)
            else:
                print >>sys.stderr, exc
            return None
        receiver = self.makeReceiver(sock, addr, w_ok=False)
        self.incoming[sock.fileno()] = receiver
        return receiver

    def listen(self, addr):
        self.listener = socket.socket()
        self.listener.bind(addr)
        self.listener.setblocking(0)
        self.listener.listen(1)
        if self.verbose:
            print 'listening on', addr

    def shutdown(self, timeout):
        self.timeout = timeout

    def close(self, fileno):
        receiver = self.incoming.pop(fileno)
        receiver.close()

    def doAccept(self):
        try:
            conn, addr = self.listener.accept()
        except socket.error:
            return
        if self.verbose:
            print 'connection', addr
        conn.setblocking(0)
        if self.ssl:
            conn = ssl.wrap_socket(conn, server_side=True, **self.ssl_kw)
        self.incoming[conn.fileno()] = self.makeReceiver(conn, addr)

    def nop(self):
        pass

    def wait(self):
        r_all, w_all = [], []
        for r in self.incoming.values():
            if r.w_ok:
                r_all.append(r)
            if r.write or not r.w_ok:
                w_all.append(r)
        if self.timeout is not None and not r_all:
            return []
        if self.listener is not None:
            r_all.append(self.listener)
        if self.loop_out is not None:
            r_all.append(self.loop_out)
        work = []
        try:
            r_ok, w_ok, e_ok = select.select(r_all, w_all, [], self.timeout)
        except KeyboardInterrupt:
            if self.verbose:
                print 'shutdown via keyboard interrupt'
            work.append((self.onShutdown,))
            r_ok, w_ok = [], []
        for sock in w_ok:
            work.append((sock.doSend,))
        for sock in r_ok:
            if sock is self.listener:
                work.append((self.doAccept,))
            elif sock is self.loop_out:
                with self.lock:
                    work.extend(self.todo)
                    self.todo = []
                data = sock.recv(1)
                if data == '':
                    if self.verbose:
                        print 'shutdown via loopback'
                    sock.close()
                    self.loop_out = None
                    work.append((self.onShutdown,))
                else:
                    work.append((self.nop,))
            else:
                work.append((sock.doRecv,))
        return work

    def start(self):
        self.timeout = None
        self.loop_in, self.loop_out = socket.socketpair()

    def stop(self):
        self.loop_in.close() # wakes select, recv() -> ''
        self.loop_in = None

    def cleanup(self):
        if self.verbose:
            print 'doing cleanup'
        if self.listener is not None:
            self.listener.close()
            self.listener = None
        for receiver in self.incoming.values():
            receiver.close()
        self.incoming = {}

    def connected(self, receiver):
        # Implement me to do something when a receiver is connected.
        pass

    def disconnected(self, receiver):
        # Implement me to do something when a receiver is disconnected.
        pass

    def makeReceiver(self, conn, addr, w_ok=True):
        # Override me to return a subclass of the BaseReceiver.
        return BaseReceiver(conn, addr, self, w_ok)

    def onShutdown(self):
        # Override me to do application-level shutdown.
        self.shutdown(0.5)

