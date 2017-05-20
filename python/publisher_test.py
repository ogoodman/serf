#!/usr/bin/python

"""Tests for publisher module."""

import unittest
import weakref
import types
from serf.publisher import Publisher, PERSISTENT, WEAK
from serf.storage import Storage
from serf.bound_method import BoundMethod

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
        self._save()

    def onEvent(self, event, info):
        self.events.append(info + 20)
        self._save()

    def on(self, *args):
        self.events.append(args)
        self._save()

    def _save(self):
        pass

class SubAdapter(object):
    def __init__(self, event, subscriber, func):
        """Make a subscriber equivalent to lambda e, i: func(subscriber, e, i)."""
        self.event = event
        self.subscriber = weakref.ref(subscriber)
        self.func = func
        self.how = WEAK

    def wants(self, event):
        return event == self.event

    def notify(self, event, info):
        """Calls func(subscriber, event, info) if subscriber is still live."""
        subscriber = self.subscriber()
        if subscriber is None:
            return False
        self.func(subscriber, event, info)

    def handle(self):
        return self.subscriber()

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

        # Adapt the subscriber (add 10 to each event info).
        sub = Subscriber(events)
        asub = SubAdapter('info', sub, lambda s, e, i: s(e, i+10))
        pub.addSub(asub)
        del asub

        pub.notify('info', 1)
        del sub
        pub.notify('info', 2)

        # Only adapted event 1 arrives before asub dies with sub.
        self.assertEqual(events, [11])

        # Adapt the subscribing method (add 10 to each event info).
        sub = Subscriber(events)
        asub = SubAdapter('info', sub, lambda s, e, i: s.onEvent(e, i+10))
        pub.addSub(asub)
        del asub

        pub.notify('info', 1)
        del sub
        pub.notify('info', 2)

        # Only adapted event 1 arrives before asub dies with sub.
        self.assertEqual(events, [11, 31])

    def testPersistence(self):
        store = {}
        storage = Storage(store)

        storage['pub'] = p = Publisher()
        storage['sub'] = s = Subscriber([])

        p.subscribe('snap', s.onEvent, how=PERSISTENT)
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

    def testArgs(self):
        # Non-persistent.
        events = []
        def cb(*args):
            events.append(args)

        p = Publisher()
        p.subscribe('done', cb, args=('x', 42))
        p.notify('done', True)

        self.assertEqual(events, [('done', True, 'x', 42)])

        # Persistent.
        store = {}
        storage = Storage(store)

        storage['sub'] = s = Subscriber([])
        sid = p.subscribe('dusted', s.on, args=('hello',), how=PERSISTENT)
        storage['pub'] = p

        del s, p

        p = storage['pub']
        p.notify('dusted', 14)

        # FIXME: a tuple is converted to a list here. That's a
        # serializer bug.
        self.assertEqual(storage['sub'].events, [['dusted', 14, 'hello']])

        p.unsubscribe('dusted', sid, how=PERSISTENT)
        p.notify('dusted', 15)
        self.assertEqual(len(storage['sub'].events), 1)

    def testCatchAllSubscriptions(self):
        # Persistent.
        store = {}
        storage = Storage(store)

        storage['pub'] = p = Publisher()
        storage['sub'] = s = Subscriber([])

        sid = p.subscribe('*', s.on, args=('hello',), how=PERSISTENT)

        del s, p

        p = storage['pub']
        p.notify('dusted', 14)

        # FIXME: a tuple is converted to a list here. That's a
        # serializer bug.
        self.assertEqual(storage['sub'].events, [['dusted', 14, 'hello']])

        p.unsubscribe('*', sid, how=PERSISTENT)
        p.notify('dusted', 15)
        self.assertEqual(len(storage['sub'].events), 1)

    def testLazyInfo(self):
        s = Subscriber([])
        p = Publisher()
        p.subscribe('bar', s.on)

        self.info_calls = 0
        def info():
            self.info_calls += 1
            return {'n': 42}

        # no subscribers to 'foo' so info won't be called.
        p.notify('foo', info)
        self.assertEqual(s.events, [])
        self.assertEqual(self.info_calls, 0)

        p.notify('bar', info)
        self.assertEqual(s.events, [('bar', {'n': 42})])
        self.assertEqual(self.info_calls, 1)


if __name__ == '__main__':
    unittest.main()
