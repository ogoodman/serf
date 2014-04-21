#!/usr/bin/env python

"""Handy stuff for the command line."""

import os
import sys
import time
from eventlet.green import select
from code import InteractiveConsole
from fred.fs_dict import FSDict
from fred.vat import Vat
from fred.eventlet_net import Net
from fred.node import Node
from fred.eventlet_thread import EventletThread
from fred.proxy import Proxy
from fred.util import timeCall, codeDir
from fred.po.printer import Printer
from fred.po.group import Group
from fred.storage import Storage, fcat
from fred.worker import Worker
from fred.repl_proxy import REPLProxy

# A basic problem here (and with all code which uses eventlet in
# the Python REPL) is that raw_input does a blocking read which prevents
# any work from happening in the eventlet main thread Hub.
# This is a particular problem when input may be received at any
# time through the Net object. The peer created in the REPL will be
# unable to respond. This module implements two partial fixes.
#
# 1. Run the Net and main Vat in a thread. Wrap all references to these
#    objects in a proxy that transfers all calls into their thread.
#
# 2. Use code.InteractiveConsole to set up a replica of Python's REPL
#    and override raw_input to do eventlet.green.select which does
#    not block the main thread's Hub. This would be a very good solution
#    if it didn't break readline editing of REPL input. (Running this
#    script via rlwrap works though.)
#
# We will use the wrapping approach if this module is imported and
# the InteractiveConsole approach if it is run as a script.

RUN_CONSOLE = (__name__ == '__main__')

SERVER = '127.0.0.1:6502'
CLIENT = '127.0.0.1:6503'

CERT = os.path.join(codeDir(), 'data/host.cert')
KEY = os.path.join(codeDir(), 'data/host.key')

store = FSDict(os.path.join(codeDir(), 'data/client'))

net = Net(CLIENT, use_ssl=True, keyfile=KEY, certfile=CERT)
node = Node(CLIENT, net, store)

thread = EventletThread()
s0 = Storage(store, '0', node, t_model=thread)
v0 = Vat(CLIENT, '0', s0, t_model=thread)
node.addVat(v0)
s0.rpc = v0

# thread.start(True) means start a new thread, while False means
# use the current thread. When RUN_CONSOLE is true we run Net and Vat
# calls in the main thread.
thread.start(not RUN_CONSOLE)

thread.callFromThread(net.listen)
thread.callFromThread(net.start)

# A second thread for testing blocking code.
s1 = Storage(store, '1', node, t_model=EventletThread())
v1 = Vat(CLIENT, '1', s1, t_model=s1.thread_model)
node.addVat(v1)
s1.rpc = v1
s1.thread_model.start(True)

def wrap(x):
    return REPLProxy(x, thread)

o = s0.getn('o')
ro = s0.getn('o-remote')
p = s0.getn('printer')
server = s0.getn('server')

class ClientConsole(InteractiveConsole):
    def raw_input(self, prompt):
        sys.stdout.write(prompt)
        sys.stdout.flush()
        select.select([sys.stdin],[],[])
        s = sys.stdin.readline()
        if not s:
            raise EOFError()
        return s.strip()

if RUN_CONSOLE:
    console = ClientConsole(locals())
    console.interact()
else:
    o, ro, p, server, s0 = map(wrap, [o, ro, p, server, s0])
