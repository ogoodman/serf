"""Mock proxy types for use in testing."""

from serf.util import EqualityMixin

class SProxy(EqualityMixin):
    def __init__(self, arg):
        self.arg = arg

class Proxy(EqualityMixin):
    def __init__(self, arg):
        self.arg = arg

class MockProxyFactory(object):
    def toProxy(self, sp):
        return Proxy(sp.arg)

    def isSProxy(self, sp):
        return type(sp) is SProxy

    def isProxy(self, p):
        return type(p) is Proxy

    def toSProxy(self, p):
        return SProxy(p.arg)
