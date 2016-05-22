"""Tests for ws_transport module."""

import unittest
from cStringIO import StringIO
from ws_transport import BinaryHandler, Decoder, SocketBuffer

class FakeSocket(object):
    def __init__(self, incoming):
        self.incoming = incoming

    def recv(self, n):
        # It is our responsibility in setting up the test
        # to know how many times recv will be called and with what n.
        data = self.incoming[0]
        if n < len(data):
            data, self.incoming[0] = data[:n], data[n:]
        else:
            self.incoming.pop(0)
        return data

class WSTransportTest(unittest.TestCase):
    def testBinaryHandler(self):
        out = StringIO()
        binaries = {'fred': out}
        handler = BinaryHandler(binaries)
        handler.write('fr')
        handler.write('ed:and som')
        handler.write('e more')
        self.assertEquals(out.getvalue(), 'and some more')
        handler.close()
        self.assertTrue(out.closed)

    def testDecoder(self):
        out = StringIO()
        mask = [0, 1, 0, 1]
        decoder = Decoder(mask, out)
        decoder.write('I am fred')
        decoder.write(' I am george')
        encoded = out.getvalue()
        self.assertEquals(encoded, 'I!al grdd!I!al fenrfe')

        # Repeat should decode.
        out = StringIO()
        decoder = Decoder(mask, out)
        decoder.write(encoded)
        self.assertEquals(out.getvalue(), 'I am fred I am george')
        decoder.close()
        self.assertTrue(out.closed)

    def testSocketBuffer(self):
        socket = FakeSocket(['ab', 'cdef', 'g::hijkl', 'mnop'])
        buf = SocketBuffer(socket)
        self.assertEquals(buf.read(2), 'ab')
        self.assertEquals(buf.readTo('::'), 'cdefg::')
        self.assertEquals(buf.read(6), 'hijklm')
        self.assertEquals(buf.read(3), 'nop')

        sink = StringIO()
        socket = FakeSocket(['ab', 'cdef', 'g::hijkl', 'mnop'])
        buf = SocketBuffer(socket)
        self.assertEquals(buf.readTo('::'), 'abcdefg::')
        self.assertEquals(buf.read(6, sink), 'hijklm')
        self.assertEquals(sink.getvalue(), 'hijklm')


if __name__ == '__main__':
    unittest.main()
