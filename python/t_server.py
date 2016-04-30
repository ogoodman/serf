#!/usr/bin/python

"""Server that hosts a table."""

from serf.transport import Transport
from serf.eventlet_thread import EventletThread
from serf.rpc_handler import RPCHandler
from serf.tables.table import Table
from serf.po.printer import Printer

NODE = '127.0.0.1:6506'

class ProxyCaller(object):
    def do_say(self, proxy):
        print 'proxy', str(proxy)
        proxy.say('hi')
    def call(self, proxy):
        proxy(42)

def func(a):
    print 'func', a

transport = Transport(NODE)
objects = {
    'table': Table(None, 'table'),
    'printer': Printer(),
    'proxy_caller': ProxyCaller(),
    'func': func,
}
thread = EventletThread()

rpc = RPCHandler(transport, objects, thread)
rpc.safe.append('serf.tables')

thread.start()
print 'Serf Server 0.1', NODE
transport.serve()
thread.stop()
