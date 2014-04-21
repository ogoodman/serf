"""Serializable File reference."""

import os

def _seek(fh, pos, rel_end):
    if rel_end:
        fh.seek(pos, os.SEEK_END)
    else:
        fh.seek(pos, os.SEEK_SET)

# Stateless interface to a file. The file itself has state but
# there are no seek or tell methods.

class File(object):
    serialize = ('_vat', 'path',)

    def __init__(self, vat, path):
        self.vat = vat
        self.path = path
        self._size = -1
        
    def read(self, n=-1, pos=0, rel_end=None):
        if rel_end is None:
            rel_end = (pos < 0) # default to start for pos==0
        fh = self._open('rb')
        _seek(fh, pos, rel_end)
        return fh.read(n)

    def readNT(self, n=-1, pos=0, rel_end=None):
        if rel_end is None:
            rel_end = (pos < 0) # default to start for pos==0
        try:
            return self.read(n, pos, rel_end)
        except IOError:
            return ''

    def write(self, data, pos=0, rel_end=None):
        if rel_end is None:
            rel_end = (pos <= 0) # default to append for pos==0
        fh = self._open('r+b')
        _seek(fh, pos, rel_end)
        fh.write(data)
        if self._size >= 0:
            fh.seek(0, os.SEEK_END)
            self._size = fh.tell()

    def truncate(self, pos=0, rel_end=None):
        if rel_end is None:
            rel_end = (pos < 0) # default to start for pos==0
        fh = self._open('r+b')
        _seek(fh, pos, rel_end)
        fh.truncate()
        self._size = fh.tell()

    def size(self):
        if self._size >= 0:
            return self._size
        fh = self._open('rb')
        _seek(fh, 0, True)
        self._size = fh.tell()
        return self._size

    def sizeNT(self):
        try:
            return self.size()
        except IOError:
            return 0

    def erase(self):
        self.vat.store.erase(self.path)
        self._size = -1

    def exists(self):
        return self.vat.store.exists(self.path)

    def open(self):
        # If we make FileHandle network serializable, then code
        # can use file.open() network transparently and still
        # obtain file-like objects.
        # The FileHandle uses readNT so effectively open appears
        # to automatically create an empty file.
        return FileHandle(self)

    def _open(self, mode='r+b'):
        return self.vat.store.open(self.path, mode)

# Python file-like object which can be used to adapt a remote File
# instance to code expecting a file handle.

class FileHandle(object):
    serialize = ('file',)

    def __init__(self, file):
        self.file = file
        self.pos = 0

    def seek(self, pos, rel=os.SEEK_SET):
        if rel == os.SEEK_END:
            assert(pos <= 0)
            self.pos = self.file.size() + pos
        elif rel == os.SEEK_CUR:
            self.pos += pos
        else:
            assert(rel == os.SEEK_SET)
            self.pos = pos

    def tell(self):
        return self.pos

    def read(self, n=-1):
        data = self.file.readNT(n, self.pos)
        self.pos += len(data)
        return data

    def write(self, data):
        self.file.write(data, self.pos, False)
        self.pos += len(data)

    def truncate(self):
        self.file.truncate(self.pos)

def openFile(file):
    # Network transparent file-opening which is as efficient as
    # possible when the file object is a local reference.
    try:
        return file._open()
    except AttributeError:
        return FileHandle(file)

class TestFile(File):
    def __init__(self):
        self._fh = None
        self._size = -1

    def _open(self, mode='r+b'):
        if self._fh is None:
            if mode == 'rb':
                raise IOError(2, os.strerror(2))
            self._fh = os.tmpfile()
        return self._fh

    def erase(self):
        if self._fh is None:
            raise OSError(2, os.strerror(2))
        self._fh = None

    def exists(self):
        return self._fh is not None

