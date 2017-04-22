#!/usr/bin/python

import weakref
from serf.publisher import Publisher

class OnlineList(Publisher):
    def __init__(self, factory):
        """Create an online list with an online entity factory.

        Args:
            factory

        The factory must have a make() method for making new online
        entities.

        The factory must have an init() method which we call passing
        ourself so that the factory can keep a reference to us and
        set up any subscriptions it requires.
        """
        Publisher.__init__(self)
        self.online = weakref.WeakValueDictionary()
        self.factory = factory
        self.factory.init(self)

    def add(self, client_addr):
        """Call to create a new online entity when a connection appears."""
        online = self.factory.make()
        self.online[client_addr] = online
        self.notify('online', [client_addr, online])
        return online

    def remove(self, client_addr):
        """Call to initiate cleanup when a connection is closed."""
        try:
            online = self.online.pop(client_addr)
            self.notify('offline', [client_addr, online])
        except KeyError:
            pass

    def items(self):
        """Allows the caller to obtain the list of online entities."""
        return self.online.items()
