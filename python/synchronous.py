"""Synchronous thread-model for use in tests."""

class Result(object):
    def __init__(self, main_loop=None):
        self.result = None
        self.exc = None
        self.called = False

    def success(self, result):
        self.result = result
        self.called = True

    def failure(self, exc):
        self.exc = exc
        self.called = True

    def wait(self):
        if not self.called:
            raise Exception('Callback not called.')
        if self.exc is not None:
            raise self.exc
        return self.result

class Synchronous(object):
    def callFromThread(self, func, *args):
        func(*args)

    def call(self, func, *args):
        func(*args)

    def makeCallback(self):
        return Result()

