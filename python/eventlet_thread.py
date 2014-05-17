"""Adapts Eventlet GreenThreads to our ThreadModel interface."""

import atexit
import eventlet
import threading
from eventlet.event import Event
from eventlet.green import socket

class EventletCallback(object):
    def __init__(self):
        self.event = Event()

    def wait(self):
        with eventlet.Timeout(10):
            return self.event.wait()

    def success(self, result):
        self.event.send(result)

    def failure(self, exc):
        self.event.send_exception(exc)

class EventletThread(object):
    def __init__(self):
        self.loop_in = None
        self.loop_out = None
        self.lock = None
        self.queue = []
        self.thread = None
        atexit.register(self.stop)

    def start(self, thread=False):
        self.loop_in, self.loop_out = socket.socketpair()
        self.lock = threading.Lock()
        if thread:
            assert(self.thread is None)
            self.thread = threading.Thread(target=self.run)
            self.thread.setDaemon(True)
            self.thread.start()
        else:
            eventlet.spawn_n(self.run)

    def run(self):
        while self.loop_out.recv(1):
            with self.lock:
                work, self.queue = self.queue, []
            for args in work:
                eventlet.spawn_n(*args)

    def call(self, *args):
        eventlet.spawn_n(*args)

    def callAfter(self, secs, *args):
        return eventlet.spawn_after(secs, *args)

    def stop(self):
        if self.loop_in:
            self.loop_in.close()
            self.loop_in = None
        if self.thread is not None:
            self.thread.join()
            self.thread = None

    def makeCallback(self):
        return EventletCallback()

    def callFromThread(self, *args):
        # FIXME: some code is calling this when it doesn't need to.
        # Some other code is patching this to self.call because
        # it doesn't need to start the thread. There is a simpler
        # thread model than this that uses an existing reactor and
        # might not even need callFromThread to handle other threads.
        with self.lock:
            self.queue.append(args)
        self.loop_in.send('\x01')
