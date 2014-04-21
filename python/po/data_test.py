#!/usr/bin/python

"""Tests for Data object which wraps and observes changes to plain-old-data."""

import unittest
from serf.po.data import Data, AutoSave
from serf.synchronous import Synchronous
from serf.green_thread import GreenThread
from serf.worker import Callback
from serf.proxy import Proxy

class TestObserver(object):
    def __init__(self):
        self.update = None

    def add(self, path, new):
        self.update = ('add', path, new)

    def change(self, path, old, new):
        self.update = ('change', path, old, new)

    def delete(self, path, old):
        self.update = ('delete', path, old)

class TestStore(object):
    def __init__(self):
        self.count = 0
        self.value = None

    def _set(self, data):
        self.value = data.copy()
        self.count += 1

class DataTest(unittest.TestCase):
    def test(self):
        obs = TestObserver()
        data = Data(['a', {'x': [1,2,3], 'y': {'u': 1, 'v':[]}}, []])
        data.obs._add(obs)

        self.assertEqual(data[0], 'a')
        self.assertEqual(type(data[1]), Data)
        self.assertEqual(data[1]['x'][0], 1)

        data[1]['x'][0] = 4
        self.assertEqual(obs.update, ('change', [1, 'x', 0], 1, 4))

        data[1]['x'] = [4, 5]
        self.assertEqual(obs.update, ('change', [1, 'x'], [4, 2, 3], [4, 5]))

        data[1]['x'].append(6)
        self.assertEqual(obs.update, ('add', [1, 'x', 2], 6))

        data[1]['x'].insert(0, 3)
        self.assertEqual(obs.update, ('add', [1, 'x', 0], 3))
        self.assertEqual(data[1]['x'].copy(), [3, 4, 5, 6])

        del data[1]['x'][1]
        self.assertEqual(obs.update, ('delete', [1, 'x', 1], 4))
        self.assertEqual(data[1]['x'].copy(), [3, 5, 6])

        data[1]['x'].insert(-1, 5.5)
        self.assertEqual(obs.update, ('add', [1, 'x', -1], 5.5))
        self.assertEqual(data[1]['x'].copy(), [3, 5, 5.5, 6])

        del data[1]['y']['u']
        self.assertEqual(obs.update, ('delete', [1, 'y', 'u'], 1))
        self.assertEqual(data[1]['y'].copy(), {'v': []})

        data[1]['y']['w'] = 'B'
        self.assertEqual(obs.update, ('add', [1, 'y', 'w'], 'B'))

    def testReplication(self):
        data = Data(['a', {'x': [1,2,3], 'y': {'u': 1, 'v':[]}}, []])
        repl = Data(['a', {'x': [1,2,3], 'y': {'u': 1, 'v':[]}}, []])
        data.obs._add(repl) # make repl follow data.

        data[1]['x'][0] = 4
        data[1]['x'] = [4, 5]
        data[1]['x'].append(6)
        data[1]['x'].insert(0, 3)
        del data[1]['x'][1]

        data[1]['x'].insert(-1, 5.5)
        del data[1]['y']['u']
        data[1]['y']['w'] = 'B'

        self.assertEqual(data.value, repl.value)

    def testSubDataNotAllowed(self):
        data = Data([])
        self.assertRaises(ValueError, Data, [data]) # can't construct nested
        self.assertRaises(ValueError, data.append, Data(1))
        data = Data({})
        self.assertRaises(ValueError, data.__setitem__, 'a', Data(1))
        data = Data({'a':1})
        self.assertRaises(ValueError, data.__setitem__, 'a', Data(2))

    def testAutoSave(self):
        store = TestStore()
        data = Data({})
        data.ref = store

        data['name'] = 'Fred'
        self.assertEqual(store.count, 0) # no save yet
        data.save()
        self.assertEqual(store.count, 1)
        self.assertEqual(store.value, {'name': 'Fred'})

        sync = Synchronous()
        saver = AutoSave(data, sync)
        data.change_obs._add(saver)

        # with a synchronous save, every update is saved immediately
        data['age'] = 25
        self.assertEqual(store.count, 2)
        self.assertEqual(store.value['age'], 25)
        data['age'] = 26
        self.assertEqual(store.count, 3)
        self.assertEqual(store.value['age'], 26)

        # remove it, back to manual saving.
        data.change_obs._remove(saver)
        data['age'] = 27
        self.assertEqual(store.count, 3)
        self.assertEqual(store.value['age'], 26)

        # green-threads are more efficient since a save will be done
        # only once per yield.

        green = GreenThread()
        green.start()
        saver = AutoSave(data, green)
        data.change_obs._add(saver)

        cb = Callback()

        def makeUpdates():
            data['age'] = 28
            data['pet'] = 'Fido'
            data['address'] = 'Wiltshire'
            cb.success(None)

        green.callFromThread(makeUpdates)
        cb.wait()

        self.assertEqual(store.count, 4)
        self.assertEqual(store.value['address'], 'Wiltshire')

        green.stop()

    def testSlaveAndObserverChangesAreSaved(self):
        store = TestStore()
        data = Data({})
        data.ref = store
        sync = Synchronous()
        saver = AutoSave(data, sync)
        data.change_obs._add(saver)

        data['name'] = 'Fred'
        self.assertEqual(store.count, 1)

        # Add observer
        data.obs._add(Proxy('A', 'obs'))
        self.assertEqual(store.count, 2)

        # Call slave update methods.
        data.add(['age'], 42)
        self.assertEqual(store.count, 3)

        data.change(['name'], 'Fred', 'Barney')
        self.assertEqual(store.count, 4)

        data.delete(['age'], 42)
        self.assertEqual(store.count, 5)

        # Remove observer
        data.obs._remove(Proxy('A', 'obs'))
        self.assertEqual(store.count, 6)
        self.assertEqual(len(data.obs.group), 0)

    def testDeepChangeIsSaved(self):
        data = Data({})
        data.ref = TestStore()
        sync = Synchronous()
        data.change_obs._add(AutoSave(data, Synchronous()))

        data['list'] = []
        self.assertEqual(data.ref.count, 1)
        data['list'].append(3)
        self.assertEqual(data.ref.count, 2)

if __name__ == '__main__':
    unittest.main()
