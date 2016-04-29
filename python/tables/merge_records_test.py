import unittest
from datetime import datetime
from merge_records import mergeRecords, mergeSpec
from serf.serializer import encodes, decodes

def copy(rec):
    return decodes(encodes(rec))


class MergeRecordsTest(unittest.TestCase):
    def test(self):
        now = datetime.utcnow()
        l = {'name': 'Fred', 'state': 'vic', 'age': 34, 'updated': now}

        r = {'name': 'Fido', 'age': 3, 'category': 9}
        v = {}
        w = {}

        # Merge values from L first then R.
        o = mergeRecords(1, l, 2, r, mergeSpec('L:* R:*'), copy(v))
        self.assertEqual(o['name'], 'Fred')

        # Merge values from L then R with a sensible prefix.
        o = mergeRecords(
            1, l, 2, r, mergeSpec('L:* R:*->pet_%'), copy(v))
        self.assertEqual(o['name'], 'Fred')
        self.assertEqual(o['pet_name'], 'Fido')
        self.assertEqual(o['pet_category'], 9)

        # Merge age from R, then L, the the rest of R.
        o = mergeRecords(
            1, l, 2, r, mergeSpec('R:age L:* R:*'), copy(v))
        self.assertEqual(o['age'], 3)

        # Drop age and updated from L, merge rest of L followed by R.
        o = mergeRecords(
            1, l, 2, r, mergeSpec('L:age->. L:updated->. L:* R:*'), copy(v))
        self.assertEqual(o['age'], 3)
        self.assertTrue('updated' not in o)

        # Adds the primary keys.
        o = mergeRecords(
            1, l, 2, r, 
            mergeSpec('L:#->l_pk R:#->r_pk R:* L:name->owner'), copy(v))
        self.assertEqual(o['l_pk'], 1)
        self.assertEqual(o['r_pk'], 2)
        self.assertEqual(o['owner'], 'Fred')

        # Specifying a non-existent input key.
        o = mergeRecords(
            1, l, 2, r, mergeSpec('L:address R:* L:name->owner'), copy(v))
        self.assertTrue('address' not in o)
        self.assertEqual(o['owner'], 'Fred')


if __name__ == '__main__':
    unittest.main()
