"""Tests for Collection of persistent objects."""

import unittest
from serf.tables.collection import Collection
from serf.tables.query import QTerm
from serf.publisher import Publisher
from serf.storage import Storage, save_fn


class Person(Publisher):
    serialize = ('name', 'age', '_subs')

    def __init__(self, name, age, subs=None):
        Publisher.__init__(self, subs)
        self.name = name
        self.age = age

    _save = save_fn

    def setName(self, name):
        self.name = name
        self.notify('update', {'name': name})
        self._save()

    def setAge(self, age):
        self.age = age
        self.notify('update', {'age': age})
        self._save()

    def getId(self):
        return self.ref._path

    def getInfo(self):
        return {'name': self.name, 'age': self.age}


class CollectionTest(unittest.TestCase):
    def test(self):
        storage = Storage({})

        t = storage.makeRef(Person('Tom', 3))
        d = storage.makeRef(Person('Dick', 3))

        storage['c'] = c = Collection(storage)

        c.add(t)
        c.add(d)

        self.assertEqual(len(c.values()), 2)

        del c
        self.assertEqual(storage.cache.values(), [])

        t.setAge(4)

        c = storage['c']

        # The info for Tom in c has been updated.
        self.assertEqual(c.count(QTerm(':age', 'eq', 4)), 1)

        ti = c.values(QTerm(':name', 'eq', 'Tom'))[0]
        self.assertEqual(ti['age'], 4)

        c.discard(t)

        self.assertEqual(c.count(), 1)
        self.assertEqual(len(t.subscribers('update')), 0)

        d = c.get(QTerm(':name', 'eq', 'Dick'))

        self.assertEqual(d.age, 3)


if __name__ == '__main__':
    unittest.main()
