"""Reliably replicate calls to a remote node."""

from serf.po.call_log_reader import CallLogReader
from serf.po.data_log import DataLog

class CallLog(object):
    serialize = ('_vat', 'data_log', 'readers')

    def __init__(self, vat, data_log=None, readers=None):
        self.vat = vat
        self.data_log = DataLog(vat) if data_log is None else data_log
        self.readers = readers or {}

    def __getattr__(self, name):
        def _log_call(*args):
            self.data_log.append((name, args))
        return _log_call

    def __getitem__(self, i):
        return self.data_log[i]

    def addObserver(self, obs):
        self.data_log.addObserver(obs)

    def removeObserver(self, obs):
        self.data_log.removeObserver(obs)

    def addReader(self, key, proxy, pos=None):
        if pos is None:
            pos = self.data_log.end()
        reader = CallLogReader(self.vat, self.ref, proxy, pos)
        self.readers[key] = self.vat.makeRef(reader)
        self._save()
        return reader

    def getReader(self, key):
        return self.readers[key]

    def removeReader(self, key):
        reader = self.readers.pop(key)
        reader.cleanup()
        reader._erase()

    def _save(self):
        pass

    def _on_addref(self):
        pass

    def begin(self):
        return self.data_log.begin()

    def end(self):
        return self.data_log.end()
