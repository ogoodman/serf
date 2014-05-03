import sys, traceback
import struct
from base64 import b64encode
from hashlib import sha1
from mimetools import Message
from cStringIO import StringIO
from serf.publisher import Publisher
from serf.weak_list import WeakList

CURRENT = WeakList()

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

    def __init__(self, sock, address):
        Publisher.__init__(self)
        self.sock = SocketBuffer(sock)
        self.client_address = address
        self.client_ip = address[0]
        #self.node_id = '%s:%s' % address
        self.node_id = 'server'
        self.path = ''
        self.close_sent = False
        CURRENT.add(self)

    def handle(self):
        if not self.handshake():
            return
        while self.read_next_message():
            pass

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
            self.on_close()
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
        self.notify('message', {'from': self.client_ip, 'pcol': 'json', 'message': message})

    def on_close(self):
        self.notify('close', None)

    def on_handshake(self):
        self.notify('handshake', None)

