#!/usr/local/bin/python2.6

import unittest
from datetime import datetime
from serf.obj import obj
from query import *

def matchQuery(query, rec):
    return query.match(rec)

class QueryTest(unittest.TestCase):

    def testSetMember(self):
        rec = {'id': 99}
        self.assertTrue(setMember(rec, ':id', 100))
        self.assertEquals(rec, {'id': 100})

        rec = obj(name='Fred')
        self.assertTrue(setMember(rec, '@name', 'Frederick'))
        self.assertEquals(rec.name, 'Frederick')

        rec = [1, 2, 3]
        self.assertTrue(setMember(rec, '#1', 42))
        self.assertEquals(rec, [1, 42, 3])

        rec = (0, obj(name='Barney'), {'id': 55})
        self.assertFalse(setMember(rec, '#0', 1))
        self.assertTrue(setMember(rec, '#1@name', 'Betty'))
        self.assertTrue(setMember(rec, '#2:id', 61))
        self.assertEquals(rec[0], 0)
        self.assertEquals(rec[1].name, 'Betty')
        self.assertEquals(rec[2], {'id': 61})
        
    def testSimpleStrQuery(self):
        rec = {'name': 'test1'}

        self.assertTrue(matchQuery(QTerm(':name', 'eq', 'test1'), rec))
        self.assertFalse(matchQuery(QTerm(':name', 'eq', 'test2'), rec))
        self.assertTrue(matchQuery(QTerm(':name', 'ne', 'test2'), rec))
        self.assertFalse(matchQuery(QTerm(':name', 'ne', 'test1'), rec))

        self.assertTrue(matchQuery(QTerm(':name', 'like', 'test'), rec))
        self.assertFalse(matchQuery(QTerm(':name', 'like', 'tust'), rec))
        self.assertFalse(matchQuery(QTerm(':name', 'unlike', 'test'), rec))
        self.assertTrue(matchQuery(QTerm(':name', 'unlike', 'tust'), rec))

        self.assertTrue(matchQuery(QTerm(':name', 'le', 'test2'), rec))
        self.assertFalse(matchQuery(QTerm(':name', 'ge', 'test2'), rec))
    
        self.assertTrue(matchQuery(QTerm(':name', 'notnull'), rec))
        self.assertFalse(matchQuery(QTerm(':name', 'isnull'), rec))

        rec = {'name': 'TEst1'}

        self.assertTrue(matchQuery(QTerm(':name', 'like', 'teST'), rec))
        self.assertFalse(matchQuery(QTerm(':name', 'like', 'tUST'), rec))
        self.assertFalse(matchQuery(QTerm(':name', 'unlike', 'tesT'), rec))
        self.assertTrue(matchQuery(QTerm(':name', 'unlike', 'TUST'), rec))

    def testSimpleNumeric(self):
        rec = {'age': 18}

        self.assertTrue(matchQuery(QTerm(':age', 'eq', 18), rec))
        self.assertFalse(matchQuery(QTerm(':age', 'ne', 18), rec))
        self.assertFalse(matchQuery(QTerm(':age', 'eq', 19), rec))
        self.assertTrue(matchQuery(QTerm(':age', 'ne', 19), rec))

        self.assertTrue(matchQuery(QTerm(':age', 'ge', 18), rec))
        self.assertTrue(matchQuery(QTerm(':age', 'le', 18), rec))
        self.assertFalse(matchQuery(QTerm(':age', 'ge', 19), rec))
        self.assertTrue(matchQuery(QTerm(':age', 'le', 19), rec))
        self.assertTrue(matchQuery(QTerm(':age', 'ge', 17), rec))
        self.assertFalse(matchQuery(QTerm(':age', 'le', 17), rec))
    
        self.assertFalse(matchQuery(QTerm(':age', 'eq', 18.5), rec))
        self.assertTrue(matchQuery(QTerm(':age', 'ne', 18.5), rec))
        self.assertFalse(matchQuery(QTerm(':age', 'ge', 18.5), rec))
        self.assertTrue(matchQuery(QTerm(':age', 'le', 18.5), rec))

    def testSimpleTime(self):
        dt = datetime(year=2010, month=12, day=1, hour=1)
        rec = {'due': dt}
        
        self.assertTrue(matchQuery(QTerm(':due', 'eq', dt), rec))

        later = dt + timedelta(hours=1)

        self.assertTrue(matchQuery(QTerm(':due', 'le', later), rec))
        self.assertFalse(matchQuery(QTerm(':due', 'ge', later), rec))

        # Order comparisons with wrong type are always false
        self.assertFalse(matchQuery(QTerm(':due', 'le', 1461478401), rec))
        self.assertFalse(matchQuery(QTerm(':due', 'ge', 1461478401), rec))

    def testQueriesAndOr(self) :
        tom = {'age': 18, 'gender': 'M'}
        lucy = {'age': 18, 'gender': 'F'}
        bubs = {'age': 3, 'gender': 'M'}

        male = QTerm(':gender', 'eq', 'M')
        adult = QTerm(':age', 'ge', 18)
        female = QTerm(':gender', 'eq', 'F')

        self.assertTrue(matchQuery(QAnd([male, adult]), tom))
        self.assertFalse(matchQuery(QAnd([male, adult]), lucy))
        self.assertFalse(matchQuery(QAnd([male, adult]), bubs))
        
        self.assertTrue(matchQuery(QOr([male, adult]), lucy))
        self.assertTrue(matchQuery(QOr([male, adult]), bubs))

        self.assertFalse(matchQuery(QOr([female, adult]), bubs))
        self.assertTrue(matchQuery(QAnd([male, QNot(adult)]), bubs))
   
    def testMissingField(self):
        rec = {}

        self.assertTrue(matchQuery(QTerm(':field', 'isnull'), rec))
        self.assertFalse(matchQuery(QTerm(':field', 'notnull'), rec))

        self.assertFalse(matchQuery(QTerm(':field', 'le', 0), rec))
        self.assertFalse(matchQuery(QTerm(':field', 'ge', 0), rec))

        # Matches None.
        self.assertTrue(matchQuery(QTerm(':field', 'eq'), rec))

    def testWrongType(self):
        rec = {'status': 2}

        self.assertFalse(matchQuery(QTerm(':status', 'eq', '2'), rec))
        self.assertFalse(matchQuery(QTerm(':status', 'le', '2'), rec))
        self.assertFalse(matchQuery(QTerm(':status', 'ge', '2'), rec))
        
    def testNoQuery(self):
        rec = {}
        
        self.assertTrue(matchQuery(QAnd([]), rec))
        self.assertFalse(matchQuery(QOr([]), rec))
        self.assertTrue(matchQuery(QAlways(True), rec))
        self.assertFalse(matchQuery(QAlways(False), rec))

    def testInvalidQuery(self):
        self.assertRaises(ValueError, QTerm, ':x', 'like', 14)
        self.assertRaises(ValueError, QTerm, ':x', 'unlike', 14)
        self.assertRaises(ValueError, QTerm, ':x', 'isnull', 14)
        self.assertRaises(ValueError, QTerm, ':x', 'notnull', 14)

    def testDateQuery(self):
        # match specific date of any year
        q = QDate(':dob', day=18, month=7)
        rec = {'dob': datetime(1965, 7, 18)}
        self.assertTrue(matchQuery(q, rec))
        rec['dob'] = datetime(1967, 6, 2)
        self.assertFalse(matchQuery(q, rec))

        # match specific date relative to end of month
        q = QDate(':dob', day=-1, month=3) # last day of Feb.
        rec['dob'] = datetime(1999, 2, 28)
        self.assertTrue(matchQuery(q, rec)) # not leap-year, so 28 is last.
        rec['dob'] = datetime(2000, 2, 28)
        self.assertFalse(matchQuery(q, rec)) # leap-year, so 28 is not last.
        rec['dob'] = datetime(2000, 2, 29)
        self.assertTrue(matchQuery(q, rec)) # leap-year, so 29 is last.

        # match any day in a given month
        q = QDate(':dob', month=3)
        rec['dob'] = datetime(2005, 3, 15)
        self.assertTrue(matchQuery(q, rec))
        rec['dob'] = datetime(2005, 5, 15)
        self.assertFalse(matchQuery(q, rec))

        # match specific date in any month
        q = QDate(':dob', day=8)
        rec['dob'] = datetime(2005, 12, 8)
        self.assertTrue(matchQuery(q, rec))
        rec['dob'] = datetime(2005, 12, 5)
        self.assertFalse(matchQuery(q, rec))

        # match last day of any month
        q = QDate(':dob', day=-1)
        rec['dob'] = datetime(2000, 2, 29)
        self.assertTrue(matchQuery(q, rec))
        rec['dob'] = datetime(2000, 12, 31)
        self.assertTrue(matchQuery(q, rec))
        rec['dob'] = datetime(2000, 1, 1)
        self.assertFalse(matchQuery(q, rec))

        # exact date
        q = QDate(':dob', 1965, 7, 18)
        rec['dob'] = datetime(1965, 7, 18)
        self.assertTrue(matchQuery(q, rec))
        rec['dob'] = datetime(1967, 7, 18)
        self.assertFalse(matchQuery(q, rec))

if __name__ == '__main__' :
    unittest.main()
