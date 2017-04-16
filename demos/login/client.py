"""Code to interact with the login server from a python shell.

Usage:

  $ python
  ...
  >>> from client import *
  >>> admin.addUser('fred', 's3cr3t')
  >>> fred = login.login('fred', 's3cr3t')

The 'fred' value is a proxy to a persistent UserCaps object to which
we can add 'capabilities', other persistent objects that are available
to the 'fred' user for getting things done.
"""

from serf.rpc_handler import RPCHandler
from serf.transport import Transport
from serf.eventlet_thread import EventletThread
from serf.proxy import Proxy
from serf.repl_proxy import REPLProxy

SERVER = '127.0.0.1:6508'

net = Transport()

thread = EventletThread()
rpc = RPCHandler(net, {}, t_model=thread)
rpc.safe.append('serf.tables.table_handle')

def remote(x):
    return REPLProxy(rpc.makeProxy(x, SERVER), thread)

thread.start(True)

thread.callFromThread(net.start)

admin = remote('admin')
login = remote('login')
