"""Applies contents of a call log to a remote object."""

import socket

class CallLogReader(object):
    serialize = ('_env', 'data_log', 'proxy', 'pos')

    def __init__(self, env, data_log, proxy, pos):
        self.env = env
        self.data_log = data_log
        self.proxy = proxy
        if type(pos) in (int, long):
            pos_ref = env.storage().makeRef()
            pos_ref._set(pos)
            self.pos = pos_ref
        else:
            self.pos = pos
        self.node_obs = env.storage().getn('node_observer')
        self.running = False
        self._pos = self.pos._get()
        self._subscribed_to_node = False
        self._subscribed_to_log = False

    def run(self):
        if self.running:
            return
        self.running = True
        try:
            self.mainLoop()
        finally:
            self.running = False

    def _doCall(self, method, args):
        try:
            getattr(self.proxy, method)(*args)
        except socket.error:
            if self._subscribed_to_node:
                return False
            self.setNodeSubscription(True)
        else:
            self._pos += 1
            self.pos._set(self._pos)
            self.setNodeSubscription(False)
        return True

    def mainLoop(self):
        while self.running:
            try:
                method, args = self.data_log[self._pos]
            except IndexError:
                break
            else:
                if not self._doCall(method, args):
                    break

    def setNodeSubscription(self, subscribe):
        if subscribe == self._subscribed_to_node:
            return
        if subscribe:
            self.node_obs.addObserver(self.proxy._node, self.ref)
        else:
            self.node_obs.removeObserver(self.proxy._node, self.ref)
        self._subscribed_to_node = subscribe

    def subscribeToLog(self):
        if self._subscribed_to_log:
            return
        self.data_log.addObserver(self.ref)
        self._subscribed_to_log = True

    def add(self, index, value):
        # Called by data_log.
        if self.running:
            return
        if index == self._pos:
            method, args = value
            self._doCall(method, args)
        else:
            self.env.thread_model.call(self.run)

    def online(self, node):
        # Called by node_obs.
        self.env.thread_model.call(self.run)

    def stop(self):
        self.running = False
        self.setNodeSubscription(False)
        self.data_log.removeObserver(self.ref)

    def start(self):
        self.data_log.addObserver(self.ref)
        self.env.thread_model.call(self.run)

    @staticmethod
    def create(env, data_log, proxy, pos=None):
        return env.storage().makeRef(CallLogReader(env, data_log, proxy, pos))

    def cleanup(self):
        self.stop()
        self.pos._erase()
