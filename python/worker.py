"""Blocking thread-model."""

import atexit
import threading
import traceback

# The question here is: how expensive are condition variables?
# Is OK to make a new one for each callback?

class Callback(object):
    def __init__(self):
        self.cond = threading.Condition()
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

class Scheduler(object):
    def __init__(self):
        self.cond = threading.Condition()
        self.queue = []
        self.done = True

    def put(self, item):
        with self.cond:
            self.queue.append(item)
            self.cond.notify()

    def start(self):
        with self.cond:
            self.done = False

    def stop(self):
        with self.cond:
            self.done = True
            self.cond.notify()

    def wait(self):
        with self.cond:
            while not self.done and not self.queue:
                self.cond.wait()
            if self.done and not self.queue:
                return []
            items = self.queue
            self.queue = []
            return items

    def cleanup(self):
        pass

class Worker(object):
    def __init__(self, scheduler=None):
        self.thread = None
        self.scheduler = Scheduler() if scheduler is None else scheduler
        self.items = []
        atexit.register(self.stop)

    def start(self):
        assert(self.thread is None)
        self.scheduler.start()
        self.thread = threading.Thread(target=self.run)
        self.thread.setDaemon(True)
        self.thread.start()

    def callFromThread(self, *args):
        self.scheduler.put(args)

    def call(self, *args):
        self.items.append(args)

    def callTS(self, *args):
        if self.thread is None:
            func = args[0]
            func(*args[1:])
        elif self.thread == threading.currentThread():
            self.items.append(args)
        else:
            self.scheduler.put(args)

    def run(self):
        if self.thread is None:
            self.thread = threading.currentThread()
        while True:
            self.items = self.scheduler.wait()
            if not self.items:
                break
            while self.items:
                try:
                    args = self.items.pop(0)
                    func = args[0]
                    func(*args[1:])
                except:
                    traceback.print_exc()

    def stop(self):
        if self.thread is None:
            return
        self.scheduler.stop()
        self.thread.join()
        self.thread = None
        self.scheduler.cleanup()

    def makeCallback(self):
        return Callback()
