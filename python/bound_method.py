"""Represents a method which may be on a server or browser object."""

import weakref

# NOTE: check what already exists for the regular peer-to-peer
# case if anything. One possible issue with this version is that
# it does not hide the object id from anyone it is passed to.

class BoundMethod(object):
    def __init__(self, handler, oid, method, node, twoway=False):
        self.handler = weakref.ref(handler)
        self.oid = oid
        self.method = method
        self.node = node
        self.twoway = twoway

    def __call__(self, *args):
        """Make a one-way call to the referenced object's method.

        This returns None if the RPC handler is still live.
        It returns False if the handler has been garbage collected.
        """
        h = self.handler()
        if h is None:
            # False is for unsubscribing. This happens when a server
            # object has subscribers in multiple browser sessions.
            # When a client goes away we want the subscription to be
            # removed at the next call. This conflicts slightly with
            # the case where we want to use the result of a bound method.
            # Then false might be a legal value and we don't want to
            # get it just because the client has gone away.
            return False
        if self.node == h.node_id:
            h.localCall(self.oid, self.method, args)
        else:
            h.send(self.node, self.oid, {'m':self.method, 'a':list(args)})

    def _ext_encoding(self):
        return 'BoundMethod', {'o':self.oid, 'm':self.method, 'n':self.node, 't': self.twoway}
