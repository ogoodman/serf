"""Transfers messages received to the best matching endpoint."""

import json
from serf.serializer import decodes
from serf.publisher import Publisher

# NOTE: we have removed pcol from the Transport interface
# so this is probably all irrelevant now.

class Endpoint(Publisher):
    """Implements Transport. Endpoint for messages handled by a Dispatcher."""
    def __init__(self, dispatcher, node_id, path):
        Publisher.__init__(self)
        self.dispatcher = dispatcher
        self.node_id = node_id
        self.path = path.strip('/')
        if self.path:
            self.path += '/'

    def send(self, node, msg, pcol='serf', errh=None):
        self.dispatcher._send(node, msg, pcol, errh)

class Dispatcher(object):
    def __init__(self, transport):
        self.endpoints = []
        self.transport = transport
        self.transport.subscribe('message', self._handle)

    def addEndpoint(self, path):
        endpoint = Endpoint(self, self.transport.node_id, path)
        self.endpoints.append(endpoint)
        return endpoint

    def _handle(self, ev, msg):
        if msg['pcol'] == 'json':
            addr = json.loads(msg['message'])['o']
        else:
            addr = decodes(msg['message'])
        addr = addr.rstrip('/') + '/' # normalise path.
        for e in self.endpoints:
            if addr.startswith(e.path):
                e.notify(ev, msg)
                break

    def _send(self, node, msg, pcol, errh):
        self.endpoint.send(node, msg, pcol, errh)
