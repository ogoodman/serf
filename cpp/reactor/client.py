#!/usr/bin/python
from __future__ import with_statement

"""Client to test server.cpp."""

__author__ = 'oliver@insermo.com (Oliver Goodman)'

import socket
import time

sock = socket.socket()
sock.connect(('127.0.0.1', 6666))

print sock.recv(4096)
exit()

def readAll():
    count = 0
    n_reads = 0
    while True:
        bit = sock.recv(4096)
        if not bit:
            break
        count += len(bit)
        n_reads += 1
        time.sleep(0.01)
    return count, n_reads

counts = readAll()
print 'Read %d bytes in %d reads' % counts

