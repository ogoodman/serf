#!/usr/bin/python

"""Tests for Transport."""

import time
import os
import unittest
import socket
import eventlet
from serf.util import codeDir
from serf.transport import *
from serf.eventlet_test_handler import TestHandler

SERV = '127.0.0.1:6512'
NOSERV = '127.0.0.1:6514'

SSL = {
    'certfile': os.path.join(codeDir(), 'data/host.cert'),
    'keyfile': os.path.join(codeDir(), 'data/host.key'),
}

t0 = time.time()
def elapsed():
    print '  ---  ', time.time() - t0

class TransportTest(unittest.TestCase):
    def test(self):
        server = Transport(SERV, ssl=SSL)
        handler = TestHandler(server)

        client = Transport(ssl=SSL)
        c_handler = TestHandler(client)

        server.listen()
        server.start()
        with handler.expect(1):
            client.send(SERV, 'hi')
        self.assertEqual(handler.received, ['hi'])

        with c_handler.expect(1):
            server.send(handler.node_conn, 'hello') # send with server running.
        self.assertEqual(c_handler.received, ['hello'])

        def errh(exc):
            c_handler.handle('', {'message': exc})
        with c_handler.expect(1):
            client.send(NOSERV, 'anyone there?', errh=errh)
        self.assertEqual(type(c_handler.received[0]), socket.error)

        # Restart the server.
        server.stop()
        server.listen()
        server.start()

        with handler.expect(1):
            client.send(SERV, 'hello again')

        with handler.expect(3):
            client.send(SERV, 'gday')
            client.send(SERV, 'howdy')
            client.send(SERV, '')
        self.assertEqual(handler.received, ['gday', 'howdy', ''])

        server.stop()

    def testClientOffline(self):
        server = Transport(SERV)
        handler = TestHandler(server)
        server.listen()
        server.start()

        self.disconnected = None
        def on_disc(ev, info):
            self.disconnected = info
        server.subscribe('disconnected', on_disc)

        client = Transport()
        c_handler = TestHandler(client)

        with handler.expect(1):
            client.send(SERV, 'hi')
        self.assertEqual(handler.received, ['hi'])

        c_node = handler.node_conn

        with c_handler.expect(1):
            server.send(c_node, 'hello')
        self.assertEqual(c_handler.received, ['hello'])

        client.stop()

        self.assertEqual(self.disconnected, c_node)

        self.err_count = 0
        def errh(e):
            self.err_count += 1
            self.assertEqual(type(e), socket.error)
        server.send(c_node, 'hello again', errh=errh)
        self.assertEqual(self.err_count, 1)

        server.stop()

    def testGetAddr(self):
        self.assertEqual(getAddr(SERV), ('127.0.0.1', 6512))
        self.assertEqual(getAddr('fred.local'), ('fred.local', 6502))

    def testBadClient(self):
        server = Transport(SERV)
        handler = TestHandler(server)
        server.listen()
        server.start()

        client = Transport()

        # Instead of doing client.connect which would be well-behaved
        # we'll do some of the steps from there wrongly.
        sock = eventlet.connect(getAddr(SERV))
        what, ssl_opts = client.read(sock)
        self.assertEqual(what, SSL_OPTIONS)

        # Send less than a full header (5 bytes).
        sock.send('abc')
        sock.shutdown(socket.SHUT_WR) # Server will close on incomplete header.
        reply = sock.recv(1024)
        self.assertEqual(reply, '')

        # Server should have already forgotten us.
        self.assertEqual(len(server.nodes), 0)

        # Connect again: send incomplete payload.
        sock = eventlet.connect(getAddr(SERV))
        what, ssl_opts = client.read(sock)
        sock.send('\0\0abcfoo')
        sock.shutdown(socket.SHUT_WR) # Server will close on incomplete payload.
        reply = sock.recv(1024)

        # Connect again: send invalid protocol choice.
        sock = eventlet.connect(getAddr(SERV))
        what, ssl_opts = client.read(sock)
        self.assertEqual(what, SSL_OPTIONS)
        client.write(sock, SSL_CHOICE, 'R') # no such choice
        reply = sock.recv(1024) # Server will close, this won't block.
        self.assertEqual(reply, '')
        self.assertEqual(len(server.nodes), 0) # Again, no connection.

        server.stop()


if __name__ == '__main__':
    unittest.main()
