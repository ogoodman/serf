#!/usr/bin/python

"""Tests for publisher module."""

import unittest
import weakref
import types
from publisher import Publisher
from weak_list import getAdapter
from storage import Storage
from bound_method import BoundMethod

class Parent(object):
    def __init__(self, child):
        self.child = child
        self.child.subscribe('event', self.onEvent)
        self.from_child = None

    def onEvent(self, event, info):
        self.from_child = info

class Subscriber(object):
    serialize = ('events',)

    def __init__(self, events):
        self.events = events

    def __call__(self, event, info):
        self.events.append(info)

    def onEvent(self, event, info):
        self.events.append(info + 20)

class PublisherTest(unittest.TestCase):
    def testNonCyclic(self):
        # Publishers are supposed to break cyclic dependencies; we have
        # two-way communication between parent and child without the
        # child holding a reference to the parent.
        p = Parent(Publisher())

        p.child.notify('event', 'foo')
        p.child.notify('event', 'bar')
        self.assertEqual(p.from_child, 'bar')

        wp = weakref.ref(p)
        self.assertTrue(wp() is not None)
        del p
        self.assertTrue(wp() is None)

    def testAdaptSubscriber(self):
        pub = Publisher()

        events = []

        # Make a normal subscriber.
        sub = Subscriber(events)

        pub.subscribe('info', sub)

        pub.notify('info', 1)
        sub = None
        pub.notify('info', 2)
        # Only event 1 arrives before sub is dead.
        self.assertEqual(events, [1])

        # Adapt the subscriber (add 10 to each event info).
        sub = Subscriber(events)
        asub = getAdapter(sub, lambda s, e, i: s(e, i+10), 'add10')

        pub.subscribe('info', asub)
        asub = None # don't keep ref to asub.

        pub.notify('info', 1)
        sub = None
        pub.notify('info', 2)
        # Only adapted event 1 arrives before asub dies with sub.
        self.assertEqual(events, [1, 11])

        # Make a subscriber and subscribe a method
        sub = Subscriber(events)
        pub.subscribe('info', sub.onEvent)

        pub.notify('info', 1)
        sub = None
        pub.notify('info', 2)
        # Only event 1 arrives before sub is dead.
        self.assertEqual(events, [1, 11, 21])

        # Adapt the subscribing method (add 10 to each event info).
        sub = Subscriber(events)
        asub = getAdapter(sub.onEvent, lambda s, e, i: s(e, i+10), 'add10')

        pub.subscribe('info', asub)
        asub = None # don't keep ref to asub.

        pub.notify('info', 1)
        sub = None
        pub.notify('info', 2)
        # Only adapted event 1 arrives before asub dies with sub.
        self.assertEqual(events, [1, 11, 21, 31])

    def testPersistence(self):
        store = {}
        storage = Storage(store)

        storage['pub'] = p = Publisher()
        storage['sub'] = s = Subscriber([])

        p.subscribe('snap', s.onEvent, persist=True)
        p.notify('snap', 1)

        self.assertEqual(s.events, [21])

        storage['sub'] = s

        # Reboot.
        storage = Storage(store)
        p = storage['pub']

        p.notify('snap', 2)

        s = storage['sub']
        self.assertEqual(s.events, [21,22])

        del storage['sub']
        del s

        # When delivery fails, subscriber is removed.
        p.notify('snap', 3)
        self.assertEqual(len(p.subscribers('snap')), 0)


if __name__ == '__main__':
    unittest.main()
