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

WS_FRAME_CONTINUATION = 0x0
WS_FRAME_TEXT = 0x1
WS_FRAME_BINARY = 0x2
WS_FRAME_CLOSE = 0x8
WS_FRAME_PING = 0x9
WS_FRAME_PONG = 0xA

class SocketBuffer(object):
    def __init__(self, sock):
        self.sock = sock
        self.buff = ''

    def _buffer(self, n, sink=None):
        data = self.sock.recv(n)
        if not data: # at EOF
            if self.buff:
                print >>sys.stderr, 'Truncated read: expected %d got %d' % (n, len(self.buff))
            return False
        self.buff += data
        if sink is not None:
            sink.write(data)
        return True

    def read(self, n, sink=None):
        """Reads exactly n bytes from the socket.

        If the socket reaches EOF before n bytes are read, returns
        an empty string, discarding any partial read.
        """
        if sink is not None:
            sink.write(self.buff[:n])
        while len(self.buff) < n:
            if not self._buffer(n - len(self.buff), sink):
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

class Decoder(object):
    """A Decoder acts as a filter for a writable file-like object.

    Data is exclusive-or-ed with the mask which is expected
    to be an array of 4 byte-sized integers.

    :param mask: array of 4 byte sized integers
    :param out: writeable file-like object for output
    """
    def __init__(self, mask, out):
        self._mask = mask
        self._out = out
        self._n = 0

    def write(self, data):
        """Decodes the data and passes it to the output object.

        :param data: string data to be decoded
        """
        buf = ''
        for char in data:
            buf += chr(ord(char) ^ self._mask[self._n % 4])
            self._n += 1
        self._out.write(buf)

    def close(self):
        """Closes the output object."""
        self._out.close()

class BinaryHandler(object):
    """A BinaryHandler dispatches a key-prefixed binary string to a handler.

    Data is fed to the BinaryHandler via its write method.
    It is expected that the data will be prefixed with a key
    of at most 20 chars, followed by a ':'. In that case, the key
    is removed, the matching handler is popped, and remaining data
    is fed to the handler.

    :param handlers: a dictionary of handlers
    """
    def __init__(self, handlers):
        self._handlers = handlers
        self._key = ''
        self._handler = None
        self._ok = True
        self._done = 0

    def write(self, data):
        self._done += len(data)

        # We look for a key delimited by a ':' within the first
        # 20 chars of the binary data. If found we call a handler
        # which has hopefully been registered in advance.
        if self._ok and self._handler is None:
            self._key += data
            pos = self._key[:20].find(':')
            if pos < 0:
                if len(self._key) >= 21:
                    self._ok = False
            else:
                # Found a ':'.
                self._key, data = self._key[:pos], self._key[pos + 1:]
                if self._key in self._handlers:
                    self._handler = self._handlers.pop(self._key)
                else:
                    self._ok = False

        # pass data on to the handler
        if self._handler is not None:
            try:
                self._handler.write(data)
            except Exception, e:
                print 'Handler for binary with key:', self._key, 'raised:', e
                self._handler = None

    def close(self):
        if self._handler is None:
            print 'Discarded %d bytes of data' % self._done
        else:
            self._handler.close()

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
        self.binaries = {}

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

        # If it's not binary we decode it immediately.
        if ctrl != WS_FRAME_BINARY:
            decoded = ''
            for char in self.sock.read(length):
                decoded += chr(ord(char) ^ masks[len(decoded) % 4])

        if ctrl == WS_FRAME_CLOSE:
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
        elif ctrl == WS_FRAME_BINARY:
            sink = Decoder(masks, BinaryHandler(self.binaries))
            self.sock.read(length, sink)
            sink.close()
        elif ctrl == WS_FRAME_TEXT:
            self.on_message(decoded)
        return True

    def add_binary_handler(self, key, handler):
        """Sets a handler to receive a binary message.

        A handler must have 'write' and 'close' methods.
        The key must be at most 20 chars long and not contain a ':'.
        When a binary message is received, prefixed with a matching
        key followed by a ':', the remainder of the message is fed
        to the matching handler.

        :param key: key under which to store a handler
        :param handler: handler to store
        """
        self.binaries[key] = handler

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
