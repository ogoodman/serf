"""Object for running tests with."""

class TestObject(object):
    serialize = ('received', 'proxy')

    def __init__(self, received=None, proxy=None):
        self.received = received or []
        self.proxy = proxy

    def incr(self, n):
        return n + 1

    def setProxy(self, proxy):
        self.proxy = proxy
        self._save()

    def callIncr(self, n):
        return self.proxy.incr(n)

    def callTime(self):
        return 'TestObject.callTime: ' + self.proxy.time()

    def setName(self, name):
        self.proxy['name'] = name

    def _save(self):
        pass
