#!/usr/bin/env python

"""Handy stuff for the command line."""

import os
import sys
import time

from serf.rpc_handler import RPCHandler
from serf.transport import Transport
from serf.eventlet_thread import EventletThread
from serf.proxy import Proxy
from serf.repl_proxy import REPLProxy
from serf.po.printer import Printer

from serf.tables.table import *
from serf.tables.query import *

SERVER = '127.0.0.1:6506'

transport = Transport()
thread = EventletThread()
rpc = RPCHandler(transport, {}, t_model=thread)
rpc.safe.append('serf.tables')

def proxy(name):
    return REPLProxy(Proxy(SERVER, name, rpc), thread)

# thread.start(True) means start a new thread.
thread.start(True)
thread.callFromThread(transport.start)

table = proxy('table')
