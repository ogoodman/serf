from storage import save_fn
from publisher import Publisher

class Model(Publisher):
    serialize = ('data', '_subs')

    INFO = ()

    def __init__(self, data=None, subs=None):
        Publisher.__init__(self, subs)
        self.data = data or {}

    _save = save_fn

    def value(self):
        return self.data

    def update(self, record):
        modified = {}
        for k, v in record.iteritems():
            old_v = self.data.get(k)
            if v != old_v:
                if v is None:
                    del self.data[k]
                else:
                    self.data[k] = v
                modified[k] = v
        if modified:
            self._save()
            self.notify('update', modified)
            info = {}
            for k in self.INFO:
                if k in modified:
                    info[k] = modified[k]
            if info:
                self.notify('info', info)

    def get(self, key):
        return self.data.get(key)

    def getId(self):
        return self.ref._path

    def getInfo(self):
        info = {}
        for k in self.INFO:
            info[k] = self.data.get(k)
        return info
