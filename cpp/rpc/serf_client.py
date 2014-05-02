#!/usr/bin/python
"""Tests the serf_server by sending it some simple input."""

import sys
import socket
import struct
import time

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

if __name__ == '__main__':
    sock = socket.create_connection(('localhost', 6669))
    # sendFragmented(sys.argv[1], sock)

    sock.send('\1\0\0\0\4NODE')
    sock.send('\0\0\0\0\5Hello')

    sock.send('\0\0\0\0\4send')

    sock.close()

