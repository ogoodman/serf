#!/usr/bin/python

"""Tests for Net."""

import time
import os
import unittest
import socket
from serf.util import codeDir
from serf.eventlet_net import Net
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

class NetTest(unittest.TestCase):
    def test(self):
        server = Net(SERV, use_ssl=True, **SSL)
        handler = TestHandler(server)

        client = Net('CLIENT', use_ssl=True, **SSL)
        c_handler = TestHandler(client)

        server.listen()
        server.start()
        with handler.expect(1):
            client.send(SERV, 'hi')
        self.assertEqual(handler.received, ['hi'])
        self.assertEqual(handler.node_conn, 'CLIENT')

        with c_handler.expect(1):
            server.send('CLIENT', 'hello') # send with server running.
        self.assertEqual(c_handler.received, ['hello'])

        def errh(exc):
            c_handler.handle('', exc)
        with c_handler.expect(1):
            client.send(NOSERV, 'anyone there?', errh=errh)
        self.assertEqual(type(c_handler.received[0]), socket.error)

        # Restart the server.
        server.stop()
        server.listen()
        server.start()

        with handler.expect(1):
            client.send(SERV, 'hello again')

        with handler.expect(2):
            client.send(SERV, 'gday')
            client.send(SERV, 'howdy')
        self.assertEqual(handler.received, ['gday', 'howdy'])

        server.stop()


if __name__ == '__main__':
    unittest.main()
