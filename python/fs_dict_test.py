#!/usr/bin/python

"""Tests for FSDict."""

import os
import shutil
import unittest
from serf.fs_dict import FSDict
from serf.util import codeDir

class MyTest(unittest.TestCase):
    def test(self):
        root = os.path.join(codeDir(), 'test_dir')
        fs = FSDict(root)
        fs['a/b'] = 'fred'
        self.assertEqual(fs['a/b'], 'fred')
        self.assertTrue('a/b' in fs)
        del fs['a/b']
        self.assertRaises(KeyError, fs.__getitem__, 'a/b')
        self.assertTrue('a/b' not in fs)
        self.assertRaises(KeyError, fs.__delitem__, 'a/b')

        # Test it is really the file system :-)
        fs['a/c'] = 'barney'
        fs = FSDict(root) # New one.
        self.assertEqual(fs['a/c'], 'barney')

        shutil.rmtree(root)

    def testOpen(self):
        root = os.path.join(codeDir(), 'test_dir')
        fs = FSDict(root)

        self.assertRaises(AssertionError, fs.open, '../stuff', 'r+b')
        self.assertRaises(AssertionError, fs.open, '/foo', 'rb')

        fh = fs.open('d/f1', 'r+b')
        fh.write('one')
        fh.write('two')

        fh = fs.open('d/f1', 'rb')
        self.assertEqual(fh.read(), 'onetwo')
        fh.seek(3, os.SEEK_SET)
        self.assertEqual(fh.read(), 'two')
        del fh

        self.assertTrue(fs.exists('d/f1'))
        fs.erase('d/f1')
        self.assertFalse(fs.exists('d/f1'))
        
        self.assertRaises(IOError, fs.open, 'd/f1', 'rb')

        shutil.rmtree(root, ignore_errors=True)

if __name__ == '__main__':
    unittest.main()
