"""Mock persistent storage base."""

import os

class TestFS(object):
    def __init__(self):
        self.files = {}
        self.handles = {}

    def __setitem__(self, path, value):
        self.files[path] = value

    def __getitem__(self, path):
        return self.files[path]

    def __delitem__(self, path):
        del self.files[path]

    def open(self, path, mode):
        assert(mode in ('rb', 'r+b'))
        if path not in self.handles:
            if mode == 'rb':
                raise IOError(2, os.strerror(2))
            self.handles[path] = os.tmpfile()
        return self.handles[path]

    def erase(self, path):
        if path in self.handles:
            del self.handles[path]
        else:
            raise OSError(2, os.strerror(2))

    def exists(self, path):
        return path in self.handles
