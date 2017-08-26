import unittest
from serf.storage import Storage
from serf.publisher import PERSISTENT
from serf.publisher_test import Subscriber
from serf.tables.table import KeyValueChange
from serf.tables.collection_model import CollectionModel
from serf.model import Model

class Person(Model):
    INFO = ('name', 'age')
class People(CollectionModel):
    INFO = ('name',)

class CollectionModelTest(unittest.TestCase):
    def test(self):
        storage = Storage({})
        storage['s'] = s = Subscriber([])
        storage['c'] = c = People(storage, {'name': 'Kids', 'area': 3056})
        storage['t'] = t = Person({'name': 'Tom', 'age': 3})

        # Subscriptions to a CollectionModel go to both
        # the underlying Table and Model.

        sid = c.subscribe('*', s.on, how=PERSISTENT)

        c.add(t)

        del s, c, t
        s = storage['s']
        c = storage['c']
        t = storage['t']

        self.assertEqual(c.value()['name'], 'Kids')

        c.update({'name': 'Children'})
        c.update({'area': 3057})
        t.update({'age': 4})

        # Check that the Collection has tracked the age change.
        self.assertEqual(len(c.values()), 1)
        self.assertEqual(c.values()[0]['age'], 4)

        # NOTE: for each update to the table we get 4 events,
        # 'change', 'change_r', 'key:x' and 'key_r:x'. Normally we
        # would use a more selective subscription but for the test
        # it is convenient to capture them all.

        # Here we expect 2*4 = 8 Table events, plus 3 from the
        # Model aspect of the CollectionModel.
        self.assertEqual(len(s.events), 11)

        changes = [i for e, i in s.events if e == 'change']
        self.assertEqual(len(changes), 2)
        self.assertEqual(changes[0].old, None)
        self.assertEqual(changes[0].value['age'], 3)
        self.assertEqual(changes[1].old['age'], 3)
        self.assertEqual(changes[1].value['age'], 4)

        updates = [i for e, i in s.events if e == 'update']
        self.assertEqual(len(updates), 2)
        self.assertTrue({'name': 'Children'} in updates)
        self.assertTrue({'area': 3057} in updates)

        info = [i for e, i in s.events if e == 'info']
        self.assertEqual(info, [{'name': 'Children'}])

        # Check that both Table and Model subscriptions
        # are properly removed via the one subscription id.

        c.unsubscribe('*', sid, how=PERSISTENT)

        c.update({'name': 'Playgroup'})
        t.update({'age': 5})

        self.assertEqual(len(s.events), 11) # no new events

        self.assertEqual(c.values()[0]['age'], 5)

        c.discard(t)

        self.assertEqual(len(c.values()), 0)

if __name__ == '__main__':
    unittest.main()
