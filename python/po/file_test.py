#!/usr/bin/python

"""Tests for File and FileHandle."""

import unittest
import os
from serf.po.file import File, FileHandle, TestFile
from serf.test_fs import TestFS
from serf.fs_dict import FSDict
from serf.obj import obj
from serf.util import codeDir

DATA_DIR = os.path.join(codeDir(), 'test_data')

class FileTest(unittest.TestCase):
    def tearDown(self):
        p = os.path.join(DATA_DIR, 'files', 'test')
        if os.path.exists(p):
            os.unlink(p)

    def testFile(self):
        vat = obj(store=TestFS())
        # vat = obj(store=FSDict(DATA_DIR))
        test = File(vat, 'test')
        # test = TestFile()

        self.assertFalse(test.exists())
        self.assertRaises(IOError, test.size)
        self.assertRaises(IOError, test.read)
        self.assertRaises(OSError, test.erase)

        self.assertEqual(test.readNT(), '')
        self.assertEqual(test.sizeNT(), 0)
        self.assertEqual(test.exists(), False) # NT methods don't create a file.

        test.write('one') # creates automatically
        self.assertTrue(test.exists())
        self.assertEqual(test.size(), 3)
        self.assertEqual(test.read(), 'one')
        self.assertEqual(test.read(1), 'o')
        self.assertEqual(test.read(1, 1), 'n')
        self.assertEqual(test.read(1, -1), 'e')

        self.assertEqual(test.sizeNT(), 3)
        self.assertEqual(test.readNT(), 'one')

        test.write('two') # defaults to append
        self.assertEqual(test.read(), 'onetwo')
        self.assertEqual(test.size(), 6)

        test.write('three', 3) # overwrite from pos==3
        self.assertEqual(test.read(), 'onethree')
        test.write('irty', -3) # overwrite 3 before end.
        self.assertEqual(test.read(), 'onethirty')
        test.write('two', 0, rel_end=False) # overwrite 'one'
        self.assertEqual(test.read(), 'twothirty')
        test.write('wen', -5)
        self.assertEqual(test.read(), 'twotwenty')

        test.truncate(8)
        self.assertEqual(test.read(), 'twotwent')
        self.assertEqual(test.size(), 8)
        test.truncate(-1)
        self.assertEqual(test.read(), 'twotwen')
        self.assertEqual(test.size(), 7)
        test.truncate()
        self.assertEqual(test.read(), '')
        self.assertEqual(test.size(), 0)
        self.assertTrue(test.exists())
        
        test.erase()
        self.assertFalse(test.exists())

    def testOpenFile(self):
        # vat = obj(store=TestFS())
        vat = obj(store=FSDict(DATA_DIR))
        # test = File(vat, 'test')
        test = TestFile()
        # fh = test._open()
        fh = FileHandle(test)
        # fh = os.tmpfile()

        self.assertEqual(fh.tell(), 0)
        self.assertEqual(fh.read(), '')
        fh.write('one')
        self.assertEqual(fh.tell(), 3)
        fh.seek(0)
        self.assertEqual(fh.read(1), 'o')
        self.assertEqual(fh.tell(), 1)
        self.assertEqual(fh.read(1), 'n')
        self.assertEqual(fh.tell(), 2)
        self.assertEqual(fh.read(), 'e')
        self.assertEqual(fh.tell(), 3)

        fh.write('two')
        fh.seek(0)
        self.assertEqual(fh.read(), 'onetwo')
        fh.seek(-3, os.SEEK_END)
        self.assertEqual(fh.read(), 'two')
        fh.seek(0)
        self.assertEqual(fh.read(1), 'o')
        fh.seek(1, os.SEEK_CUR)
        self.assertEqual(fh.read(1), 'e')

        fh.seek(-3, os.SEEK_END)
        fh.truncate()
        self.assertEqual(fh.tell(), 3)
        fh.seek(0)
        self.assertEqual(fh.read(), 'one')


if __name__ == '__main__':
    unittest.main()
