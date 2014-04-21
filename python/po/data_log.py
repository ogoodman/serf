"""Same as LogFile but stores serializable data structures."""

from fred.serialize import encodes, decodes
from fred.po.log_file import LogFile
from fred.po.group import Group

class DataLog(object):
    serialize = ('_vat', 'fh', 'obs')

    def __init__(self, vat, fh=None, obs=None, begin=0, bm_gap=None):
        self.vat = vat
        self.fh = vat.makeFile() if fh is None else fh
        self.obs = Group() if obs is None else obs
        self.log = LogFile(self.fh, begin, bm_gap)
        self.ref = None

    def __getitem__(self, i):
        return decodes(self.log[i], self.vat.decode)

    def __getslice__(self, i, j):
        return [decodes(s, self.vat.decode) for s in self.log[i:j]]

    def append(self, value):
        index = self.log.append(encodes(value, self.vat.encode))
        self.obs.add(index, value)
        return index

    def begin(self):
        return self.log.begin()

    def end(self):
        return self.log.end()

    def addObserver(self, obs):
        self.obs._add(obs)
        self._save()

    def removeObserver(self, obs):
        self.obs._remove(obs)
        self._save()

    def _save(self):
        pass
