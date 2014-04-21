"""Object for running tests with."""

class TestObject(object):
    serialize = ()

    def __init__(self):
        self.received = []
        self.proxy = None

    def incr(self, n):
        return n + 1

    def setProxy(self, proxy):
        self.proxy = proxy

    def callIncr(self, n):
        return self.proxy.incr(n)

    def callTime(self):
        return 'TestObject.callTime: ' + self.proxy.time()

    def setName(self, name):
        self.proxy['name'] = name
