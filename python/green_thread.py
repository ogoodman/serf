"""Test of how green threads work."""

import atexit
from greenlet import greenlet
import threading
import traceback
from serf.worker import Worker, Scheduler, Callback
from eventlet.green import threading as green_threading

class Future(object):
    def __init__(self, thread):
        self.result = None
        self.exc = None
        self.called = False
        self.thread = thread
        self.resume = None

    def success(self, result):
        self.result = result
        self.called = True
        if self.resume is not None:
            self.thread.call(greenlet.getcurrent())
            self.resume.switch()

    def failure(self, exc):
        self.exc = exc
        self.called = True
        if self.resume is not None:
            self.thread.call(greenlet.getcurrent())
            self.resume.switch()

    def wait(self):
        # green thread version: if I have not been called with a result
        # or exception, save my green thread and switch to the main loop.
        # when called, switch to the saved green thread.
        if not self.called:
            self.resume = greenlet.getcurrent()
            self.thread.main.switch()
        if self.exc is not None:
            raise self.exc
        return self.result

class GreenCallback(object):
    def __init__(self):
        self.cond = green_threading.Condition()
        self.called = False
        self.result = None
        self.exc = None

    def success(self, result):
        with self.cond:
            self.result = result
            self.called = True
            self.cond.notify()

    def failure(self, exc):
        with self.cond:
            self.exc = exc
            self.called = True
            self.cond.notify()

    def wait(self):
        with self.cond:
            if not self.called:
                self.cond.wait(10)
            if not self.called:
                raise Exception('timeout')
            if self.exc is not None:
                raise self.exc
            return self.result

class GreenThread(Worker):
    def makeCallback(self):
        return Future(self)

    def run(self):
        self.main = greenlet.getcurrent()
        while True:
            self.items = self.scheduler.wait()
            if not self.items:
                break
            while self.items:
                try:
                    args = self.items.pop(0)
                    if type(args[0]) is greenlet:
                        args[0].switch()
                    else:
                        green = greenlet(args[0])
                        green.switch(*args[1:])
                except:
                    traceback.print_exc()

class TSGreenThread(GreenThread):
    def call(self, *args):
        if self.thread != threading.currentThread():
            self.scheduler.put(args)
        else:
            self.items.append(args)

    def makeCallback(self):
        if self.thread != threading.currentThread():
            return GreenCallback()
        return Future(self)

