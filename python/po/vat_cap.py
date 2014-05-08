"""Exposes some vat methods as a capability."""

from serf.po.printer import Printer

class RPCHandlerCap(object):
    serialize = ('_vat',)

    def __init__(self, vat):
        self.vat = vat

    def getn(self, name):
        return self.vat.getn(name)

    def setn(self, name, value):
        self.vat.setn(name, value)

    def monitorNode(self, node, monitor=True):
        nob = self.vat.getn('node_observer')
        if monitor:
            nob.addObserver(node, Printer())
        else:
            nob.removeObserver(node, Printer())

    def makeFile(self):
        return self.vat.makeRef(self.vat.makeFile())

    def echo(self, a):
        print a
