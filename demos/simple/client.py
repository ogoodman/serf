#!/usr/bin/env python

"""Handy stuff for the command line."""

import os
import sys
import time
import traceback
from eventlet.green import select
from code import InteractiveConsole
from serf.fs_dict import FSDict
from serf.rpc_handler import RPCHandler
from serf.transport import Transport
from serf.eventlet_thread import EventletThread
from serf.proxy import Proxy
from serf.util import timeCall, codeDir, dataRoot
from serf.po.printer import Printer
from serf.po.group import Group
from serf.storage import Storage, fcat, NoSuchName
from serf.worker import Worker
from serf.repl_proxy import REPLProxy

# A basic problem here (and with all code which uses eventlet in
# the Python REPL) is that raw_input does a blocking read which prevents
# any work from happening in the eventlet main thread Hub.
# This is a particular problem when input may be received at any
# time through the Transport object. The peer created in the REPL will be
# unable to respond. This module implements two partial fixes.
#
# 1. Run the Transport and main RPCHandler in a thread. Wrap all references to these
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

SSL = {
    'certfile': os.path.join(codeDir(), 'data/host.cert'),
    'keyfile': os.path.join(codeDir(), 'data/host.key')
}

store = FSDict(os.path.join(dataRoot(), 'client'))

net = Transport(CLIENT, ssl=SSL)

thread = EventletThread()
s0 = Storage(store)
v0 = RPCHandler(net, s0, t_model=thread)

def wrap(x):
    return REPLProxy(x, thread)

class ClientConsole(InteractiveConsole):
    def raw_input(self, prompt):
        sys.stdout.write(prompt)
        sys.stdout.flush()
        select.select([sys.stdin],[],[])
        s = sys.stdin.readline()
        if not s:
            raise EOFError()
        return s.strip()

try:
    # thread.start(True) means start a new thread, while False means
    # use the current thread. When RUN_CONSOLE is true we run Transport and RPCHandler
    # calls in the main thread.
    thread.start(not RUN_CONSOLE)

    thread.callFromThread(net.listen)
    thread.callFromThread(net.start)

    o = s0.getn('o')
    ro = s0.getn('o-remote')
    p = s0.getn('printer')
    server = s0.getn('server')

    if RUN_CONSOLE:
        console = ClientConsole(locals())
        console.interact()
    else:
        o, ro, p, server, s0 = map(wrap, [o, ro, p, server, s0])
except NoSuchName:
    pass
except:
    traceback.print_exc()
