import sys, traceback
import struct
from SocketServer import StreamRequestHandler
from base64 import b64encode
from hashlib import sha1
from mimetools import Message
from StringIO import StringIO
from publisher import Publisher

class WebSocketHandler(StreamRequestHandler, Publisher):
    magic = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'

    def __init__(self, request, client_address, server):
        Publisher.__init__(self)
        # This is the initialization in SocketServer.py minus the actual
        # main processing loop, which should not be being called in the __init__ method.
        self.request = request
        self.client_address = client_address
        self.server = server
        self.setup()
        # Instead, after construction we must call
        # self.setup()
        # try:
        #    self.handle()
        # finally:
        #    self.finish()

    def setup(self):
        StreamRequestHandler.setup(self)
        self.handshake_done = False

    def handle(self):
        while True:
            if not self.handshake_done:
                self.handshake()
            else:
                if not self.read_next_message():
                    break

    def read_next_message(self):
        data = self.rfile.read(2)
        if len(data) < 2:
            print self.client_ip, 'EOF', repr(data)
            return False
        ctrl = ord(data[0]) & 0xF
        # print 'ctrl=%d' % ctrl
        length = ord(data[1]) & 127
        if length == 126:
            length = struct.unpack(">H", self.rfile.read(2))[0]
        elif length == 127:
            length = struct.unpack(">Q", self.rfile.read(8))[0]
        masks = [ord(byte) for byte in self.rfile.read(4)]
        decoded = ""
        for char in self.rfile.read(length):
            decoded += chr(ord(char) ^ masks[len(decoded) % 4])
        if ctrl == 8:
            print self.client_ip, 'CLOSE', repr(decoded)
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

    def send(self, node, message, errh=None, code=0x81):
        self.request.send(chr(code))
        length = len(message)
        if length <= 125:
            self.request.send(chr(length))
        elif length >= 126 and length <= 65535:
            self.request.send(struct.pack('>bH', 126, length))
        else:
            self.request.send(struct.pack('>bQ', 127, length))
        self.request.send(message)

    def handshake(self):
        data = self.request.recv(1024).strip()
        headers = Message(StringIO(data.split('\r\n', 1)[1]))
        self.client_ip = headers.get('X-Forwarded-For', self.client_address[0])
        if headers.get('Upgrade', None).lower() != 'websocket':
            print self.client_ip, 'missing header "Upgrade: websocket"'
            return
        key = headers['Sec-WebSocket-Key']
        digest = b64encode(sha1(key + self.magic).hexdigest().decode('hex'))
        response = 'HTTP/1.1 101 Switching Protocols\r\n'
        response += 'Upgrade: websocket\r\n'
        response += 'Connection: Upgrade\r\n'
        response += 'Sec-WebSocket-Accept: %s\r\n\r\n' % digest
        self.handshake_done = self.request.send(response)
        if self.handshake_done:
            self.on_handshake()

    def on_message(self, message):
        self.notify('message', {'from': self.client_ip, 'pcol': 'json', 'message': message})

    def on_close(self):
        self.notify('close', None)

    def on_handshake(self):
        self.notify('handshake', None)

