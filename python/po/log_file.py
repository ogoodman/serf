"""Persistence for a sequence of strings."""

import os
import struct
from fred.po.file import openFile

class IncompleteRead(Exception):
    pass

class BadSequence(Exception):
    pass

class LogFile(object):
    serialize = ('file',)

    def __init__(self, file, begin=0, bm_gap=None):
        self.file = file
        self.fh = openFile(file)
        self.fh.seek(0, os.SEEK_SET) # open('..', 'a+b') opens at end.
        first_item, file_begin = self._readItem(False)
        if file_begin is not None:
            assert(begin == 0) # begin should only be set for new files
            self._begin = file_begin
            self.fh.seek(-8, os.SEEK_END)
            end_s = self.fh.read(8)
            self._end = struct.unpack('>q', end_s)[0] + 1
        else:
            self._begin = begin
            self._end = begin
        # Adjust to optimize seek-time v.s. memory usage
        if bm_gap is None:
            if self._end - self._begin < 2**16:
                bm_gap = 1
            else:
                bm_gap = 8
        self._bookmark_gap = bm_gap
        self._bookmarks = {}

    def _readItem(self, read=True):
        len_s = self.fh.read(4)
        if not len_s:
            return (None, None)
        item_len = struct.unpack('>I', len_s)[0]
        if read:
            item = self.fh.read(item_len)
            if len(item) != item_len:
                raise IncompleteRead()
        else:
            self.fh.seek(item_len, os.SEEK_CUR)
            item = None
        seq_s = self.fh.read(8)
        if len(seq_s) != 8:
            raise IncompleteRead()
        seq = struct.unpack('>q', seq_s)[0]
        return (item, seq)

    def _seek(self, i):
        gap = self._bookmark_gap
        b = i / gap
        if b in self._bookmarks:
            self.fh.seek(self._bookmarks[b], os.SEEK_SET)
            i0 = b * gap
        else:
            self.fh.seek(0, os.SEEK_SET)
            i0 = self._begin
        for j in xrange(i0, i):
            if j % gap == 0:
                self._bookmarks[j / gap] = self.fh.tell()
            self._readItem(False)

    def __getslice__(self, i, j):
        i = max(i, self._begin)
        j = min(j, self._end)
        self._seek(i)
        return [self._readItem()[0] for k in xrange(i, j)]

    def __getitem__(self, i):
        if i < self._begin or i >= self._end:
            raise IndexError(i)
        self._seek(i)
        item, seq = self._readItem()
        if seq != i:
            raise BadSequence('Found seq=%d at position %d' % (seq, i))
        return item

    def append(self, item):
        self.fh.seek(0, os.SEEK_END) # could omit if fh is open in 'a+'
        if self._end % self._bookmark_gap == 0:
            self._bookmarks[self._end / self._bookmark_gap] = self.fh.tell()
        self.fh.write(struct.pack('>I', len(item)))
        self.fh.write(item)
        self.fh.write(struct.pack('>q', self._end))
        self._end += 1
        return self._end - 1

    def begin(self):
        return self._begin

    def end(self):
        return self._end
