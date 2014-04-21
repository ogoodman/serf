"""Persistent dict of strings based on filesystem."""

import os

class FSDict(object):
    def __init__(self, root):
        self.root = root

    def _makedirs(self, path):
        dir = os.path.dirname(path)
        if not os.path.exists(dir):
            os.makedirs(dir)

    def __setitem__(self, path, value):
        p = os.path.join(self.root, path)
        self._makedirs(p)
        with open(p, 'w') as out:
            out.write(value)

    def __getitem__(self, path):
        p = os.path.join(self.root, path)
        try:
            return open(p).read()
        except (OSError, IOError):
            raise KeyError(path)

    def __delitem__(self, path):
        p = os.path.join(self.root, path)
        try:
            os.unlink(p)
        except OSError:
            raise KeyError(path) # ick.

    def __contains__(self, path):
        return os.path.isfile(os.path.join(self.root, path))

    def open(self, path, mode):
        assert('..' not in path and not path.startswith('/'))
        assert(mode in ('rb', 'r+b'))
        p = os.path.join(self.root, 'files', path)
        try:
            return open(p, mode)
        except IOError, err:
            if err.args[0] != 2 or mode != 'r+b':
                raise
            self._makedirs(p)
            return open(p, 'w+b')

    def erase(self, path):
        assert('..' not in path and not path.startswith('/'))
        os.unlink(os.path.join(self.root, 'files', path))

    def exists(self, path):
        assert('..' not in path and not path.startswith('/'))
        return os.path.isfile(os.path.join(self.root, 'files', path))
