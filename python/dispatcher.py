"""Transfers messages received to the best matching endpoint."""

import cjson
from serf.serialize import decodes
from serf.publisher import Publisher

class Endpoint(Publisher):
    def __init__(self, dispatcher, path):
        Publisher.__init__(self)
        self.dispatcher = dispatcher
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
        endpoint = Endpoint(self, path)
        self.endpoints.append(endpoint)
        return endpoint

    def _handle(self, ev, msg):
        if msg['pcol'] == 'json':
            addr = cjson.decode(msg['message'])['o']
        else:
            addr = decodes(msg['message'])
        addr = addr.rstrip('/') + '/' # normalise path.
        for e in self.endpoints:
            if addr.startswith(e.path):
                e.notify(ev, msg)
                break

    def _send(self, node, msg, pcol, errh):
        self.endpoint.send(node, msg, pcol, errh)
