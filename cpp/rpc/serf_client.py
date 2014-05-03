#!/usr/bin/python
"""Tests the serf_server by sending it some simple input."""

import sys
import socket
import struct
import time
from serf.vat import Vat
from serf.eventlet_net import Net
from serf.eventlet_thread import EventletThread

def sendFragmented(messages, sock):
    count = 0
    buf = ''
    for msg in messages:
        header = struct.pack('>BI', count, len(msg))
        buf += header + msg
        count += 1
    while len(buf) >= 3:
        time.sleep(.2)
        sock.send(buf[:3])
        buf = buf[3:]
    sock.send(buf)

def sendMessages():
    sock = socket.create_connection(('localhost', 6502))
    # sendFragmented(sys.argv[1], sock)

    sock.send('\1\0\0\0\4NODE')
    sock.send('\0\0\0\0\5Hello')
    sock.send('\0\0\0\0\4send')

    sock.close()

def callRemote():
    thread = EventletThread()
    thread.start()
    transport = Net('127.0.0.1:6503')
    vat = Vat('127.0.0.1:6503', '', {}, node=transport, t_model=thread)
    cb = vat.call('127.0.0.1:6502', 'OBJ', 'fun_b', [5])
    print cb.wait()

if __name__ == '__main__':
    callRemote()
