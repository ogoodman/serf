"""A few tests for Tables."""

import unittest

from serf.serializer import encodes, decodes

from notification_tracker import NotificationTracker
from table import Client, KeyValuePair, Indexer, FieldValue, CopyField, JoinSpec
from merge_records import mergeSpec
from query import *

class TableTest(unittest.TestCase):
    client = Client()

    def setUp(self):
        self.table = self.client.openDb('test/table-1')
        self.info = None
        self.all_info = []
        if self.table.size():
            self.table.erase()

    def tearDown(self):
        self.table.erase()

    def _insertPerson(self, name, age=0, id=''):
        return self.table.insert(encodes({'name': name, 'age': age, 'id': id}))

    def _insertTestData(self):
        id = self._insertPerson('Fred', 35)
        self._insertPerson('Fred', 64)
        self._insertPerson('Louise', 35)
        return id # of Fred aged 35.

    def testWeGetNotifiedOfChanges(self):
        tracker = NotificationTracker(fast=True)

        # Set notifies twice, once for change, once for the key.
        self.table.subscribe('key:100', tracker.callback)
        self.table.subscribe('change', tracker.callback)
        with tracker.expect(2):
            self.table.set(100, 'foo')

        # After unsubscribe, set notifies once.
        self.table.unsubscribe('change', tracker.callback)
        with tracker.expect(1):
            self.table.set(100, 'bar')
        self.assertEqual(tracker.events[0].value, 'bar')

        # Notification for remove has empty value.
        with tracker.expect(1):
            self.table.remove(100)
        self.assertEqual(tracker.events[0].value, '')

        # Check notification for insert.
        self.table.subscribe('change', tracker.callback)
        with tracker.expect(1):
            self.table.insert('baz')
        self.assertEqual(tracker.events[0].value, 'baz')

        # Check no notifications for insertBatch
        with tracker.expect(0):
            self.table.insertBatch(['foonly', 'garply'])

        with tracker.expect(0):
            self.table.insertNoNotify('quarply')

        with tracker.expect(0):
            self.table.setBatch([KeyValuePair(13, 'goober')])

        # Add another specific subscriber and reinsert record 100.
        with tracker.expect(2):
            self.table.subscribe('key:200', tracker.callback)
            self.table.set(100, 'quux')

        # Check we get two notifications, one "delete" with -(record-count)
        # and one for 'key:100' but none for 'key:200'.
        self.table.subscribe('delete', tracker.callback)
        size = self.table.size()
        self.all_info = []
        with tracker.expect(2):
            self.table.removeAll()
        self.assertTrue(-size in [info.key for info in tracker.events])

        # Check 'key:200' notification for pop.
        with tracker.expect(2): # key:200 and change.
            self.table.set(200, 'garply')

        self.table.unsubscribe('delete', tracker.callback)
        self.table.unsubscribe('change', tracker.callback)
        with tracker.expect(1):
            self.table.pop(200)
        self.assertEqual(tracker.events[0].key, 200)
        self.assertEqual(tracker.events[0].value, '')

        tracker.finish()

    def testChangeNotifications(self):
        tracker = NotificationTracker(fast=True)
        self.table.subscribe('change', tracker.callback)
        self.table.subscribe('delete', tracker.callback)

        def tup(kvc):
            return (kvc.key, kvc.old, kvc.value)
        def person(name, age, id):
            return encodes({'name': name, 'age': age, 'id': id})
        fred = person('fred', 10, 'F')
        barney = person('barney', 12, 'B')
        wilma = person('wilma', 14, 'W')
        betty = person('betty', 16, 'BT')
        betty17 = person('betty', 17, 'BT')
        pebble = person('pebble', 2, 'P')
        pebble3 = person('pebble', 3, 'P3')
        pebble4 = person('pebble', 4, 'P4')

        with tracker.expect(1):
            self.table.insert(fred)
        self.assertEqual(tup(tracker.events[0]), (4, '', fred))
        with tracker.expect(0):
            self.table.insertNoNotify(barney) # pkey = 8
        with tracker.expect(0):
            self.table.insertBatch([wilma]) # pkey = 12
        with tracker.expect(1):
            self.table.insertKey(':name str', betty)
        self.assertEqual(tup(tracker.events[0]), (16, '', betty))

        with tracker.expect(1):
            self.table.set(4, pebble)
        self.assertEqual(tup(tracker.events[0]), (4, fred, pebble))
        with tracker.expect(0):
            self.table.setBatch([KeyValuePair(8, pebble3)])
        with tracker.expect(2):
            self.table.setKey(':name str', pebble4)
        self.assertEqual(tup(tracker.events[0]), (8, pebble3, ''))
        self.assertEqual(tup(tracker.events[1]), (4, pebble, pebble4))
        with tracker.expect(1):
            self.table.set(8, barney)
        self.assertEqual(tup(tracker.events[0]), (8, '', barney))

        update = [FieldValue(':age', 3), FieldValue(':id', 'P3')]
        with tracker.expect(1):
            self.table.update(4, update)
        self.assertEqual(tup(tracker.events[0]), (4, pebble4, pebble3))
        with tracker.expect(1):
            self.table.updateKey(':name str', 'betty',
                                [FieldValue(':age', 17)])
        self.assertEqual(tup(tracker.events[0]), (16, betty, betty17))
        query = QTerm(':id', 'eq', 'BT')
        with tracker.expect(1):
            self.table.updateQuery(query, [FieldValue(':age', 16)])
        self.assertEqual(tup(tracker.events[0]), (16, betty17, betty))

        # For updateIter.. see testUpdateIterNotifications
        
        with tracker.expect(1):
            self.table.remove(4)
        self.assertEqual(tup(tracker.events[0]), (4, pebble3, ''))
        with tracker.expect(1):
            n = self.table.removeQuery(query) # id eq BT
        self.assertEqual(n, 1)
        self.assertEqual(tup(tracker.events[0]), (16, betty, ''))
        with tracker.expect(1):
            self.table.removeKey(':name str', 'barney')
        self.assertEqual(tup(tracker.events[0]), (8, barney, ''))
        with tracker.expect(1):
            data = self.table.pop(12)
        self.assertEqual(tup(tracker.events[0]), (12, wilma, ''))

        # Now add two more in order to test removeAll
        self.table.insertBatch([fred, barney])
        with tracker.expect(1):
            n = self.table.removeAll()
        self.assertEqual(n, 2)
        self.assertEqual(tup(tracker.events[0]), (-2, '', ''))

        tracker.finish()

    def testSetThenGet(self):
        l = self.table
        self.table.set(123, 'quux')
        self.assertEqual(self.table.select(123), 'quux')
        self.assertRaises(KeyError, self.table.select, 145)
        
    def testInsert(self):
        tracker = NotificationTracker(fast=True)

        self.table.subscribe('change', tracker.callback)
        with tracker.expect(1):
            key = self.table.insert('baz')

        self.assertEqual(tracker.events[0].key, key)
        self.assertEqual(tracker.events[0].value, 'baz')

        tracker.finish()

    def testIndexer(self):
        indexer = Indexer(':name str')
        msg = encodes({'name': 'Fred', 'age': 35})
        self.assertEqual(indexer(msg), 'Fred')
        i2 = Indexer(':name str-i')
        self.assertEqual(i2(msg), 'fred')
        i3 = Indexer(':age int')
        self.assertEqual(i3(msg), 35)

    def testInsertKey(self):
        self._insertTestData()
        tracker = NotificationTracker(fast=True)

        self.table.subscribe('change', tracker.callback)
        with tracker.expect(0):
            fred = encodes({'name': 'Fred', 'age': 5})
            pk = self.table.insertKey(':name str', fred)

        self.assertEqual(pk, -1)

        with tracker.expect(1):
            bert = encodes({'name': 'Bert', 'age': 35})
            pk = self.table.insertKey(':name str', bert)

        self.assertEqual(tracker.events[0].key, pk)
        self.assertEqual(tracker.events[0].value, bert)

        tracker.finish()

    def testRemove(self):
        self.table.set(100, 'bar')
        self.assertEqual(self.table.select(100), 'bar')
        self.table.remove(100)
        self.assertRaises(KeyError, self.table.select, 100)

    def testSetKey(self):
        self._insertTestData()
        tracker = NotificationTracker(fast=True)
        self.table.subscribe('change', tracker.callback)
        self.table.subscribe('delete', tracker.callback)

        new_fred = encodes({'name': 'Fred', 'age': 5})
        with tracker.expect(2):
            self.table.setKey(':name str', new_fred)
        self.assertEqual(self.table.pkeys(), [4, 12])
        events = [(e.key, e.value) for e in tracker.events]
        events.sort()
        self.assertEqual(events, [(4, new_fred), (8, '')])

        tracker.finish()

    def testRemoveKey(self):
        self._insertTestData()
        tracker = NotificationTracker(fast=True)
        self.table.subscribe('delete', tracker.callback)

        with tracker.expect(2):
            count = self.table.removeKey(':age int', 35)
        self.assertEqual(count, 2)
        self.assertEqual(self.table.size(), 1)
        events = [(e.key, e.value) for e in tracker.events]
        events.sort()
        self.assertEqual(events, [(4, ''), (12, '')])

        tracker.finish()

    def _fred35Query(self):
        qc1 = QTerm(':name', 'eq', 'Fred')
        qc2 = QTerm(':age', 'eq', 35)
        return QAnd([qc1, qc2])

    def testQuery(self):
        id = self._insertTestData()
        fred35 = self._fred35Query()
        count = self.table.countQuery(fred35)
        self.assertEqual(count, 1)
        results = self.table.selectQuery(fred35, 0, 100)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].key, id)

    def testSelectQueryPKR(self):
        id = self._insertTestData()
        fred35 = self._fred35Query();
        results = self.table.selectQueryPKR(fred35, 0, 100)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].key, id)

    def testSelectRange(self):
        self._insertTestData()
        results = self.table.selectRange(0, 2)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[1].key, 8)

    def testSelectAll(self):
        self._insertTestData()
        self.assertEqual(self.table.pkeys(), [4, 8, 12])
        self.assertEqual(self.table.maxId(), 12)
        results = self.table.selectAll()
        self.assertEqual(len(results), 3)

    def testSelectKey(self):
        self._insertTestData()
        results = self.table.selectKey(':name str', 'Fred')
        self.assertEqual(len(results), 2)
        results = self.table.selectKey(':age int', 64)
        self.assertEqual(len(results), 1)
        count = self.table.countKey(':name str', 'Fred')
        self.assertEqual(count, 2)
        count = self.table.countKey(':age int', 64)
        self.assertEqual(count, 1)

    def testSelectKeyRange(self):
        self._insertTestData()
        # Use selectKeyRange to pick up up to two duplicates.
        results = self.table.selectKeyRange(':name str', 'Fred', 1, 3)
        self.assertEqual(len(results), 1)

    def testFirstByKey(self):
        self._insertPerson('Brian', 39) # 4
        self._insertPerson('Albert', 45) # 8
        self._insertPerson('Alice', 25) # 12
        kvs = self.table.firstByKey(':name str')
        self.assertEqual(kvs.key, 8)
        self.assertEqual(kvs.skey, 'Albert')
        rec = decodes(kvs.value)
        self.assertEqual(rec['age'], 45)

    def testSelectUniqueKey(self):
        # This horribly mis-named method really means
        # match on a prefix and skip duplicates.
        self._insertPerson('Albert', 45) # 1st match
        self._insertPerson('Alice', 21) # 2nd match
        self._insertPerson('Alice', 25) # skipped
        self._insertPerson('Brian', 39)
        self._insertPerson('David', 55)
        count = self.table.countUniqueKey(':name str', 'Al')
        self.assertEqual(count, 2)
        results = self.table.selectUniqueKeyRange(':name str', 'Al', 1, 4)
        self.assertEqual(len(results), 1)
        rec = decodes(results[0].value)
        self.assertEqual(rec['name'], 'Alice')

    def testMatchKeyQuery(self):
        self._insertTestData()
        fred35 = self._fred35Query()
        # Another one which ought to be renamed since it has
        # nothing to do with secondary keys like the other Key methods.
        self.assertTrue(self.table.matchKeyQuery(4, fred35))
        self.assertFalse(self.table.matchKeyQuery(12, fred35))

    def testSelectText(self):
        self._insertTestData()
        kvs = self.table.selectText('Fred')
        self.assertEqual([kv.key for kv in kvs], [4, 8])
        self.assertEqual(decodes(kvs[-1].value)['age'], 64)

    def testSelectQuery(self):
        id = self._insertTestData()
        fred35 = self._fred35Query()
        results = self.table.selectQuery(fred35, 0, 100)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].key, id)
        # QText is a query term which supersedes selectText.
        fredq = QText('Fred')
        kvs = self.table.selectQuery(fredq, 0, 10)
        self.assertEqual([kv.key for kv in kvs], [4, 8])
        self.assertEqual(decodes(kvs[-1].value)['age'], 64)

    def testSelectPKR(self):
        self._insertTestData()
        results = list(self.table.selectPKR(8, 12))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].key, 8)
    
    def testDataKeyType(self):
        self.table.insert(encodes({'name': 'fred', 'id': '111'}))
        recs = self.table.selectKey(':id data', '111')
        self.assertEqual(len(recs), 1)
        self.assertEqual(decodes(recs[0].value)['name'], 'fred')
    
    def testRemoveQuery(self):
        id = self._insertTestData()
        fred35 = self._fred35Query();

        tracker = NotificationTracker()
        self.table.subscribe('delete', tracker.callback)
        with tracker.expect(1):
            count = self.table.removeQuery(fred35)

        self.assertEqual(count, 1)
        self.assertEqual(self.table.size(), 2)
        self.assertEqual(tracker.events[0].key, id)

    def testCaseInsensitiveIndex(self):
        self._insertPerson('fred', id='aaa')
        self._insertPerson('Fred', id='AAA')
        self._insertPerson('FRED', id='bbb')
        self._insertPerson('barney', id='BBB')
        self._insertPerson('Barney', id='ccc')
        self._insertPerson('BARNEY', id='CCC')

        self.assertEqual(
            self.table.countKey(':name str-i', 'fReD'), 3)
        recs = self.table.selectKey(':name str-i', 'Fred')
        self.assertEqual(len(recs), 3)
        self.assertEqual([decodes(r.value)['name'] for r in recs],
                         ['fred', 'Fred', 'FRED'])
        recs = self.table.selectKeyRange(
            ':name str-i', 'Fred', 1, 2)
        self.assertEqual(len(recs), 1)
        self.assertEqual(decodes(recs[0].value)['name'], 'Fred')

        self.assertEqual(
            self.table.countKey(':id data-i', 'bBb'), 2)

        barney = encodes({'name': 'Barney', 'id': 'ddd'})
        self.table.setKey(':name str-i', barney) # 3 barneys -> 1
        self.assertEqual(self.table.size(), 4)
        self.assertEqual(
            self.table.countKey(':id data-i', 'DDD'), 1)

        self.assertEqual(
            self.table.removeKey(':name str-i', 'fRED'), 3)
        recs = self.table.selectAll()
        self.assertEqual([decodes(r.value)['id'] for r in recs], ['ddd'])

        self._insertPerson('wilma', id='aaa')
        self._insertPerson('Wilma', id='AAA')
        self._insertPerson('WILMA', id='bbb')
        item = self.table.firstByKey(':name str-i')
        self.assertEqual(item.skey, 'barney') # skey is lowercase
        self.assertEqual(decodes(item.value)['name'], 'Barney')

    def testCISelectUniqueKey(self):
        # This is really search for a prefix in a key column.
        self._insertPerson('aaron')
        self._insertPerson('ali')
        self._insertPerson('Azalea')
        self._insertPerson('barbara')
        self._insertPerson('ALFRED')

        recs = self.table.selectUniqueKey(':name str-i', 'a')
        self.assertEqual([decodes(r.value)['name'] for r in recs],
                         ['aaron', 'ALFRED', 'ali', 'Azalea'])
        recs = self.table.selectUniqueKey(
            ':name str-i', 'al')
        self.assertEqual([decodes(r.value)['name'] for r in recs],
                         ['ALFRED', 'ali'])
        recs = self.table.selectUniqueKeyRange(
            ':name str-i', 'a', 1, 3)
        self.assertEqual([decodes(r.value)['name'] for r in recs],
                         ['ALFRED', 'ali'])
        self.assertEqual(
            self.table.countUniqueKey(':name str-i', 'a'), 4)

    def testUpdate(self):
        key = self._insertPerson('Joe', id='90')

        tracker = NotificationTracker()
        self.table.subscribe('change', tracker.callback)
        values = [FieldValue(':name', 'Joseph'), FieldValue(':age', 14)]

        with tracker.expect(1):
            self.table.update(key, values)

        rec = decodes(self.table.select(key))
        self.assertEqual(rec['name'], 'Joseph')
        self.assertEqual(rec['age'], 14)
        self.assertEqual(rec['id'], '90') # Unchanged.

        self.assertRaises(KeyError, self.table.update, key+1, values)

    def testUpdateKey(self):
        self._insertPerson('Tom', id='2')
        self._insertPerson('Dick', id='4')
        self._insertPerson('Harry', id='4')

        tracker = NotificationTracker()
        self.table.subscribe('change', tracker.callback)
        values = [FieldValue(':age', 14)]

        with tracker.expect(2):
            pkeys = self.table.updateKey(':id data', '4', values)

        self.assertEqual(pkeys, [8, 12])
        results = self.table.selectKey(':id data', '4')
        self.assertEqual([decodes(r.value)['age'] for r in results], [14, 14])

    def testUpdateQuery(self):
        self._insertPerson('Tom', id='2')
        self._insertPerson('Dick', id='4')
        self._insertPerson('Harry', id='4')

        tracker = NotificationTracker()
        self.table.subscribe('change', tracker.callback)
        values = [FieldValue(':age', 14)]

        query = QTerm(':id', 'eq', '4')
        with tracker.expect(2):
            count = self.table.updateQuery(query, values)

        self.assertEqual(count, 2)
        results = self.table.selectQuery(query, 0, 100)
        self.assertEqual([decodes(r.value)['age'] for r in results], [14, 14])

    def testUpdateQueryWithWhere(self):
        self._insertPerson('Tom', id='2')
        self._insertPerson('Dick', id='4', age=5)
        self._insertPerson('Harry', id='4')

        # Main query matches id == '4'.
        query = QTerm(':id', 'eq', '4')

        # Add a where to the FieldValue update itself.
        ageGe3 = QTerm(':age', 'ge', 3)
        pirate = QTerm(':name', 'like', 'arr')
        values = [
            FieldValue(':name', 'Oldie', ageGe3),
            FieldValue(':name', 'Pirate', pirate)]

        pkeys = self.table.updateQuery(query, values)
        names = [decodes(kv.value)['name'] for kv in self.table.selectAll()]
        self.assertEqual(names, ['Tom', 'Oldie', 'Pirate'])

    def _pet(self, name, owner, age):
        return encodes({'name': name, 'owner': owner, 'age': age})

    def testJoin(self):
        self._insertPerson('Tom', id='2', age=14)
        self._insertPerson('Dick', id='4', age=18)
        self._insertPerson('Harry', id='4', age=15)

        pets = self.client.openDb('test/pets')
        pets.set(4, self._pet('Fido', 'Tom', 3))
        pets.set(8, self._pet('Rover', 'Tom', 2))
        pets.set(12, self._pet('Oscar', 'Dick', 2))

        join = JoinSpec('name', 'owner', 'str')
        merge = mergeSpec('R:owner->. L:* R:*->pet_%')

        people = self.table.selectAll()
        results = pets.join(people, join, None, merge)
        recs = [decodes(kv.value) for kv in results]

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].key, 4)
        self.assertEqual(recs[0]['pet_name'], 'Fido')
        self.assertEqual(results[1].key, 4)
        self.assertEqual(recs[1]['pet_name'], 'Rover')
        self.assertEqual(results[2].key, 8)
        self.assertEqual(recs[2]['pet_name'], 'Oscar')

        query = QTerm(':age', 'eq', 2)

        people = self.table.selectAll()
        results = pets.join(people, join, query, merge)
        recs = [decodes(kv.value) for kv in results]

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].key, 4)
        self.assertEqual(recs[0]['pet_name'], 'Rover')
        self.assertEqual(results[1].key, 8)
        self.assertEqual(recs[1]['pet_name'], 'Oscar')

        join.nulls = True
        join.limit = 1
        join.keepOpen = True

        people = self.table.selectAll()
        results = pets.join(people, join, QAlways(True), merge)
        recs = [decodes(kv.value) for kv in results]

        self.assertEqual(len(results), 3) # exactly one per input record
        self.assertEqual(results[0].key, 4)
        self.assertEqual(recs[0]['name'], 'Tom')
        self.assertEqual(recs[0]['pet_name'], 'Fido') # enriched with first match
        self.assertEqual(results[1].key, 8)
        self.assertEqual(recs[1]['pet_name'], 'Oscar')
        self.assertEqual(results[2].key, 12)
        self.assertEqual(recs[2]['name'], 'Harry')
        self.assertTrue('pet_name' not in recs[2]) # not enriched

        results = pets.join(people, join, query, merge)
        recs = [decodes(kv.value) for kv in results]

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].key, 4)
        self.assertEqual(recs[0]['name'], 'Tom')
        self.assertEqual(recs[0]['pet_name'], 'Rover') # enriched with only match
        self.assertEqual(results[1].key, 8)
        self.assertEqual(recs[1]['pet_name'], 'Oscar')

        # people.close()

    def testJoinWithPKey(self):
        # Keys are 4, 8, 12
        self._insertPerson('Tom', id='2', age=41)
        self._insertPerson('Dick', id='4', age=45)
        self._insertPerson('Harry', id='4', age=55)

        vets = self.client.openDb('test/vets')
        vets.set(4, encodes({'practice': 'Northcote', 'person_id': 12}))
        vets.set(8, encodes({'practice': 'Brunswick', 'person_id': 4}))
        vets.set(12, encodes({'practice': 'Carlton', 'person_id': 16}))

        join = JoinSpec('#', 'person_id', 'int')
        merge = mergeSpec('L:* R:*')
        people = self.table.selectAll()
        results = vets.join(people, join, QAlways(True), merge)
        recs = [decodes(kv.value) for kv in results]

        # We stream the people in. Each person's primary key (#) is
        # used to find a vet by look-up on the person_id index.
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].key, 4)
        self.assertEqual(recs[0]['practice'], 'Brunswick')
        self.assertEqual(results[1].key, 12)
        self.assertEqual(recs[1]['practice'], 'Northcote')

        join = JoinSpec('person_id', '#', 'int')
        merge = mergeSpec('L:* R:*')
        all_vets = vets.selectAll()
        results = self.table.join(all_vets, join, QAlways(True), merge)
        recs = [decodes(kv.value) for kv in results]

        # The join is the same here but this time we're streaming
        # the vets and finding matching people by 'joining' person_id
        # in the vet stream with # (primary key lookup) in people.
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].key, 4)
        self.assertEqual(recs[0]['name'], 'Harry')
        self.assertEqual(results[1].key, 8)
        self.assertEqual(recs[1]['name'], 'Tom')

    def testJoinWithNumeric(self):
        self.table.set(4, encodes({'age': 123456789012345}))

        number = self.client.openDb('test/number')
        number.set(4, encodes({'pkey': 4}))
        numbers = number.selectAll()

        join = JoinSpec('pkey', '#', 'int')
        merge = mergeSpec('R:* R:#->pkey')

        results = self.table.join(numbers, join, None, merge)
        recs = [decodes(kv.value) for kv in results]
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]['age'], 123456789012345)

    def testUpdateIter(self):
        # Ids are 4, 8, 12.
        self._insertPerson('Tom', id='2', age=14)
        self._insertPerson('Dick', id='4', age=18)
        self._insertPerson('Harry', id='4', age=15)

        pets = self.client.openDb('test/two_pets')
        pets.set(4, self._pet('Fido', 'Tom', 3))
        pets.set(8, self._pet('Oscar', 'Dick', 2))

        # Change id to '9' and set age to the pet's age where
        # person['name'] = pets.owner
        join = JoinSpec('owner', 'name', 'str')
        values = [FieldValue(':id', '9'), CopyField(':age', ':age')]
        pet_stream = pets.selectAll()

        count = self.table.updateIter(pet_stream, join, None, values)

        self.assertEqual(count, 2)

        tom = decodes(self.table.select(4))
        self.assertEqual(tom['name'], 'Tom')
        self.assertEqual(tom['id'], '9')
        self.assertEqual(tom['age'], 3) # from Fido.

        dick = decodes(self.table.select(8))
        self.assertEqual(dick['name'], 'Dick')
        self.assertEqual(dick['id'], '9')
        self.assertEqual(dick['age'], 2) # from Oscar.

        harry = decodes(self.table.select(12))
        self.assertEqual(harry['name'], 'Harry')
        self.assertEqual(harry['id'], '4')
        self.assertEqual(harry['age'], 15)

    def testUpdateIterNotifications(self):
        tracker = NotificationTracker(fast=True)
        self.table.subscribe('change', tracker.callback)

        def tup(kvc):
            return (kvc.key, kvc.old, kvc.value)
        def person(name, age, id):
            return encodes({'name': name, 'age': age, 'id': id})
        tom = person('Tom', 14, '2')
        dick = person('Dick', 18, '4')
        harry = person('Harry', 15, '4')
        tom_u = person('Tom', 3, '9')
        dick_u = person('Dick', 2, '9')

        self.table.insertBatch([tom, dick, harry])

        pets = self.client.openDb('test/two_pets')
        pets.set(4, self._pet('Fido', 'Tom', 3))
        pets.set(8, self._pet('Oscar', 'Dick', 2))

        # Change id to '9' and set age to the pet's age where
        # person['name'] = pets.owner
        join = JoinSpec('owner', 'name', 'str')
        values = [FieldValue(':id', '9'), CopyField(':age', ':age')]
        pet_stream = pets.selectAll()

        with tracker.expect(2):
            count = self.table.updateIter(pet_stream, join, None, values)
        self.assertEqual(count, 2)
        self.assertEqual(tup(tracker.events[0]), (4, tom, tom_u))
        self.assertEqual(tup(tracker.events[1]), (8, dick, dick_u))

        tracker.finish()

    def testUpdateIterNumericKey(self):
        BIGN = 123456789101112
        rec = {'n': BIGN, 'what': 'no'}
        self.table.insert(encodes(rec))

        numeric = self.client.openDb('test/numeric')
        rec['what'] = 'match'
        numeric.set(4, encodes(rec))
        stream = numeric.selectAll()

        join = JoinSpec('n', 'n', 'int')
        values = [FieldValue(':what', 'yes')]
        self.table.updateIter(stream, join, None, values)

        updated = decodes(self.table.select(4))
        self.assertEqual(updated['what'], 'yes')

    def printResults(self, results):
        for rr in results:
            kv = decodes(rr) if type(rr) is str else rr
            print kv.key, decodes(kv.value)

    def xtestIntsetQuery(self):
        self.table.insert(encodes({'tags': set()}))
        self.table.insert(encodes({'tags': set([0])}))
        self.table.insert(encodes({'tags': set([1])}))
        self.table.insert(encodes({'tags': set([0,1])}))

        includes0 = QTerm('tags', 'includes', 0)
        includes1 = QTerm('tags', 'includes', 1)
        excludes0 = QTerm('tags', 'excludes', 0)

        results = self.table.selectQuery(includes0, 0, 10)
        keys = [kv.key for kv in results]
        self.assertEqual(keys, [8, 16])

        results = self.table.selectQuery(QOr([includes0, includes1]), 0, 10)
        keys = [kv.key for kv in results]
        self.assertEqual(keys, [8, 12, 16])

        results = self.table.selectQuery(QOr([includes1, excludes0]), 0, 10)
        keys = [kv.key for kv in results]
        self.assertEqual(keys, [4, 12, 16])

        results = self.table.selectQuery(QAnd([includes0, includes1]), 0, 10)
        keys = [kv.key for kv in results]
        self.assertEqual(keys, [16])

    def xtestBitQuery(self):
        self.table.set(3, encodes({'flags': 0x3}))
        self.table.set(5, encodes({'flags': 0x5}))
        self.table.set(6, encodes({'flags': 0x6}))

        query = QTerm('flags', 'includes', 0)
        self.assertEqual(self.queryKeys(query), [3, 5])
        query = QTerm('flags', 'excludes', 1)
        self.assertEqual(self.queryKeys(query), [5])

    def xtestIntSetUpdate(self):
        self.table.set(1, encodes({'tags': set()}))
        self.table.set(2, encodes({'tags': set([2, 3])}))

        update = [IntSetUpdate('tags', 1, True),
                  IntSetUpdate('tags', 2, False)]

        self.table.updateQuery(None, update)
        self.assertEqual(decodes(self.table.select(1))['tags'], set([1]))
        self.assertEqual(decodes(self.table.select(2))['tags'], set([1, 3]))

        # Use a global query: remove 1 if 3 is present.
        query = QTerm('tags', 'includes', 3)
        update = [IntSetUpdate('tags', 1, False)]

        self.table.updateQuery(query, update)
        self.assertEqual(decodes(self.table.select(1))['tags'], set([1]))
        self.assertEqual(decodes(self.table.select(2))['tags'], set([3]))

        # Use per-field queries: if 1 present, add 4, if 1 not present add 5.
        qi1  = QTerm('tags', 'includes', 1)
        qe1  = QTerm('tags', 'excludes', 1)
        update = [IntSetUpdate('tags', 4, True, qi1),
                  IntSetUpdate('tags', 5, True, qe1)]

        self.table.updateQuery(None, update)
        self.assertEqual(decodes(self.table.select(1))['tags'], set([1, 4]))
        self.assertEqual(decodes(self.table.select(2))['tags'], set([3, 5]))

    def xtestIntSetUpdateVar(self):
        var = {}
        var['tags'] = set()
        self.table.set(1, encodes(var))
        var['tags'] = set([2, 3])
        self.table.set(2, encodes(var))

        update = [IntSetUpdate(':tags', 1, True),
                  IntSetUpdate(':tags', 2, False)]

        self.table.updateQuery(None, update)
        self.assertEqual(decodes(self.table.select(1))['tags'], set([1]))
        self.assertEqual(decodes(self.table.select(2))['tags'], set([1, 3]))

    def xtestBitUpdate(self):
        self.table.set(1, encodes({'flags': 0}))
        self.table.set(2, encodes({'flags': 0b1100}))

        update = [IntSetUpdate(':flags', 1, True),
                  IntSetUpdate(':flags', 2, False)]

        self.table.updateQuery(None, update)
        self.assertEqual(decodes(self.table.select(1))['flags'], 0b0010)
        self.assertEqual(decodes(self.table.select(2))['flags'], 0b1010)

        # Use a global query: remove 1 if 3 is present.
        query = QTerm(':flags', 'includes', 3)
        update = [IntSetUpdate(':flags', 1, False)]

        self.table.updateQuery(query, update)
        self.assertEqual(decodes(self.table.select(1))['flags'], 0b0010)
        self.assertEqual(decodes(self.table.select(2))['flags'], 0b1000)

        # Use per-field queries: if 1 present, add 4, if 1 not present add 5.
        qi1  = QTerm(':flags', 'includes', 1)
        qe1  = QTerm(':flags', 'excludes', 1)
        update = [IntSetUpdate(':flags', 4, True, qi1),
                  IntSetUpdate(':flags', 5, True, qe1)]

        self.table.updateQuery(None, update)
        self.assertEqual(decodes(self.table.select(1))['flags'], 0b010010)
        self.assertEqual(decodes(self.table.select(2))['flags'], 0b101000)

    def queryKeys(self, query):
        return [kv.key for kv in self.table.selectQuery(query, 0, 100)]

    def testNestingQuery(self):
        self._insertPerson('Tom', age=20) # 4
        self._insertPerson('Tom', age=30) # 8
        self._insertPerson('Dick', age=20) # 12
        self._insertPerson('Dick', age=30) # 16
        self._insertPerson('Jane', age=20) # 20
        self._insertPerson('Jane', age=30) # 24

        is_jane = QTerm(':name', 'eq', 'Jane')
        not_jane = QNot(is_jane)
        age_20 = QTerm(':age', 'eq', 20)
        jane_or_20 = QOr([is_jane, age_20])
        is_tom = QTerm(':name', 'eq', 'Tom')
        tom_or_jane = QOr([is_jane, is_tom])
        jane_or_20_not_tom = QAnd([jane_or_20, QNot(is_tom)])

        self.assertEqual(self.queryKeys(is_jane), [20, 24])
        self.assertEqual(self.queryKeys(not_jane), [4, 8, 12, 16])
        self.assertEqual(self.queryKeys(age_20), [4, 12, 20])
        self.assertEqual(self.queryKeys(jane_or_20), [4, 12, 20, 24])
        self.assertEqual(self.queryKeys(is_tom), [4, 8])
        self.assertEqual(self.queryKeys(tom_or_jane), [4, 8, 20, 24])
        self.assertEqual(self.queryKeys(jane_or_20_not_tom), [12, 20, 24])

    def testIndexingBug(self):
        person = {'name': 'fred', 'age': 15}
        self.table.set(4, encodes(person))
        self.assertEqual(self.table.countKey(':name str', 'fred'), 1)
        person['name'] = 'ginger'
        self.table.set(4, encodes(person))
        self.assertEqual(self.table.countKey(':name str', 'fred'), 0)

if __name__ == '__main__':
    unittest.main()
