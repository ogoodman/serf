"""Same as LogFile but stores serializable data structures."""

from serf.serializer import encodes, decodes
from serf.storage import StorageCtx
from serf.po.log_file import LogFile
from serf.po.group import Group

class DataLog(object):
    serialize = ('_env', 'fh', 'obs')

    def __init__(self, env, fh=None, obs=None, begin=0, bm_gap=None):
        self.env = env
        self.fh = env.storage().makeFile() if fh is None else fh
        self.obs = Group() if obs is None else obs
        self.log = LogFile(self.fh, begin, bm_gap)
        self.ref = None
        self.storage_ctx = StorageCtx(self.env.storage())

    def __getitem__(self, i):
        return decodes(self.log[i], self.storage_ctx)

    def __getslice__(self, i, j):
        return [decodes(s, self.storage_ctx) for s in self.log[i:j]]

    def append(self, value):
        index = self.log.append(encodes(value, self.storage_ctx))
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
