"""Tests for TableHandle."""

import unittest
from table import *
from table_handle import TableHandle

class Subscriber(object):
    def __init__(self, events):
        self.events = events

    def onevent(self, ev, info):
        self.events.append(info)

def ageChange(info):
    return [ei['age'] for ei in info[1:]]

class TableHandleTest(unittest.TestCase):
    def testSubscribe(self):
        th = TableHandle(Table())

        events = []
        sub = Subscriber(events)
        th.subscribe('change', sub.onevent)

        th.insert(dict(name='Oliver', age=50))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[-1], [4, None, {'name':'Oliver', 'age':50}])

        th.update(PKey(4), [FieldValue(':age', 51)])
        self.assertEqual(len(events), 2)
        self.assertEqual(ageChange(events[-1]), [50, 51]) # 50 -> 51

        th.unsubscribe('change', sub.onevent) # explicit unsubscribe.
        th.update(PKey(4), [FieldValue(':age', 52)])
        self.assertEqual(len(events), 2) # no event added.

        th.subscribe('change', sub.onevent)
        th.update(PKey(4), [FieldValue(':age', 53)])
        self.assertEqual(len(events), 3) # getting events again.
        self.assertEqual(ageChange(events[-1]), [52, 53])

        sub = None # subscriber should be garbage collected immediately.
        th.update(PKey(4), [FieldValue(':age', 54)])
        self.assertEqual(len(events), 3) # no more events.


if __name__ == '__main__':
    unittest.main()
