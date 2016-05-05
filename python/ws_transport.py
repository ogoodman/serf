import sys
import traceback
import struct
import weakref
import eventlet
from base64 import b64encode
from hashlib import sha1
from mimetools import Message
from cStringIO import StringIO
from serf.publisher import Publisher
from serf.weak_list import WeakList

class SocketBuffer(object):
    def __init__(self, sock):
        self.sock = sock
        self.buff = ''

    def _buffer(self, n):
        data = self.sock.recv(n)
        if not data: # at EOF
            if self.buff:
                print >>sys.stderr, 'Truncated read %r' % self.buff
            return False
        # FIXME: this will be inefficient for very large, highly
        # fragmented reads.
        self.buff += data
        return True

    def read(self, n):
        """Reads exactly n bytes from the socket.

        If the socket reaches EOF before n bytes are read, returns
        an empty string, discarding any partial read.
        """
        while len(self.buff) < n:
            if not self._buffer(n - len(self.buff)):
                return ''
        data, self.buff = self.buff[:n], self.buff[n:]
        return data

    def readTo(self, s):
        """Reads from the socket until the string s is found.

        Returns data ending with s or an empty string if EOF reached
        before s was found.
        """
        while s not in self.buff:
            if not self._buffer(1024):
                return ''
        n = self.buff.index(s) + len(s)
        data, self.buff = self.buff[:n], self.buff[n:]
        return data

    def send(self, data):
        return self.sock.send(data)
        

class WebSocketHandler(Publisher):
    """Implements Transport. Connector for WebSocket clients."""
    magic = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'

    def __init__(self, sock, address, client_id='browser', transport=None):
        Publisher.__init__(self)
        self.sock = SocketBuffer(sock)
        self.client_address = address
        self.client_ip = address[0]
        self.node_id = 'server'
        self.client_id = client_id
        self.path = ''
        self.close_sent = False
        if transport is None:
            self.transport = weakref.proxy(self)
        else:
            self.transport = transport

    def handle(self):
        if not self.handshake():
            return
        while self.read_next_message():
            pass
        self.on_close()

    def read_next_message(self):
        data = self.sock.read(2)
        if not data:
            print self.client_ip, 'EOF', repr(data)
            return False
        ctrl = ord(data[0]) & 0xF
        length = ord(data[1]) & 127
        if length == 126:
            length = struct.unpack(">H", self.sock.read(2))[0]
        elif length == 127:
            length = struct.unpack(">Q", self.sock.read(8))[0]
        masks = [ord(byte) for byte in self.sock.read(4)]
        decoded = ""
        for char in self.sock.read(length):
            decoded += chr(ord(char) ^ masks[len(decoded) % 4])
        if ctrl == 8:
            print self.client_ip, 'CLOSE', repr(decoded)
            if self.close_sent:
                return False
            if len(decoded) >= 2:
                close_buf = decoded[:2]
            else:
                close_buf = ''
            try:
                self.send('browser', close_buf, code=0x88)
                print self.client_ip, 'sent CLOSE'
            except:
                pass
            return False
        else:
            self.on_message(decoded)
        return True

    def send(self, node, message, pcol='json', errh=None, code=0x81):
        self.sock.send(chr(code))
        length = len(message)
        if length <= 125:
            self.sock.send(chr(length))
        elif length >= 126 and length <= 65535:
            self.sock.send(struct.pack('>bH', 126, length))
        else:
            self.sock.send(struct.pack('>bQ', 127, length))
        self.sock.send(message)
        if code == 0x88:
            self.close_sent = True

    def handshake(self):
        data = self.sock.readTo('\r\n\r\n').strip()
        headers = Message(StringIO(data.split('\r\n', 1)[1]))
        if headers.get('Upgrade', None).lower() != 'websocket':
            print self.client_address, 'missing header "Upgrade: websocket"'
            return False
        self.client_ip = headers.get('X-Forwarded-For', self.client_address[0])
        key = headers['Sec-WebSocket-Key']
        digest = b64encode(sha1(key + self.magic).hexdigest().decode('hex'))
        response = 'HTTP/1.1 101 Switching Protocols\r\n'
        response += 'Upgrade: websocket\r\n'
        response += 'Connection: Upgrade\r\n'
        response += 'Sec-WebSocket-Accept: %s\r\n\r\n' % digest
        self.sock.send(response)
        self.on_handshake()
        return True

    def on_message(self, message):
        self.transport.notify('message', {'from': self.client_id, 'pcol': 'json', 'message': message})

    def on_close(self):
        self.transport.notify('close', None)

    def on_handshake(self):
        self.transport.notify('handshake', None)

class WSTransport(Publisher):
    """Implements Transport for WebSocket clients.

    If a handler is provided it will be passed each connection
    to which it can subscribe. It must call connection.handle()
    which blocks until the connection is closed.
    """
    def __init__(self, port, handler=None):
        Publisher.__init__(self)
        self.port = port
        self.handler = handler
        self.pool = eventlet.GreenPool(10000)
        self.connections = weakref.WeakValueDictionary()

    def serve(self):
        server = eventlet.listen(('0.0.0.0', self.port))
        try:
            while True:
                socket, address = server.accept()
                self.pool.spawn_n(self.handle, socket, address)
        except KeyboardInterrupt:
            for conn in self.connections.values():
                conn.send('browser', '', code=0x88) # send CLOSE.

    def handle(self, socket, address):
        node_id = '%s:%s' % address
        if self.handler is None:
            conn = WebSocketHandler(socket, address, node_id, self)
            self.connections[node_id] = conn
            conn.handle()
        else:
            conn = WebSocketHandler(socket, address)
            self.connections[node_id] = conn
            self.handler(conn)

    def send(self, node_id, msg, pcol='json', errh=None):
        handler = self.connections.get(node_id)
        if handler is None:
            print 'Send failed, node:', node_id, 'disconnected'
        else:
            handler.send(node_id, msg, pcol, errh)
