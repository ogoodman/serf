"""Free-form data for use in a storage slot."""

from fred.po.group import Group

def copy(data):
    t = type(data)
    if t is Data:
        if data.ref is not None and type(data.ref).__name__ == 'Ref':
            # convert top-level Data to Ref
            return data.ref
        raise ValueError('Data objects may not nest')
    if t.__name__ == 'Ref':
        return data
    try:
        return data.ref
    except AttributeError:
        pass
    if t is list:
        return map(copy, data)
    if t is dict:
        return dict([(k, copy(v)) for k, v in data.iteritems()])
    return data

class Data(object):
    serialize = ('value', 'obs', 'auto_save', '_vat')

    def __init__(self, value, obs=None, auto_save=True, vat=None, path=None, change_obs=None):
        self.value = copy(value) if path is None else value
        self.obs = obs if obs is not None else Group()
        self.auto_save = auto_save
        self.path = [] if path is None else path
        self.ref = None

        self.change_obs = Group() if change_obs is None else change_obs
        self.obs._obs = self.change_obs
        if self.auto_save and vat is not None:
            self.change_obs._add(AutoSave(self, vat.thread_model))

    def __setitem__(self, key, value):
        if key is None:
            old = self.value
            self.value = copy(value)
            self.obs.change([], old, value)
            self.change_obs.changed()
            return
        if type(key) is not list:
            key = [key]
        path = self.path + key
        v = self.value
        for k in key[:-1]:
            v = v[k]
        key = key[-1]
        try:
            old = v[key]
        except KeyError:
            v[key] = copy(value)
            self.obs.add(path, value)
        else:
            v[key] = copy(value)
            self.obs.change(path, old, value)
        self.change_obs.changed()

    def __delitem__(self, key):
        old = self.value.pop(key)
        self.obs.delete(self.path + [key], old)
        self.change_obs.changed()

    def __getitem__(self, key):
        if key is None:
            return self
        if type(key) is not list:
            key = [key]
        value = self.value
        for k in key:
            value = value[k]
        if type(value) in (list, dict):
            return Data(value, self.obs, path=self.path + key, change_obs=self.change_obs)
        return value

    def insert(self, pos, value):
        self.value.insert(pos, copy(value))
        self.obs.add(self.path + [pos], value)
        self.change_obs.changed()

    def append(self, value):
        self.insert(len(self.value), value)

    def copy(self):
        return copy(self.value)

    def _node(self, path):
        node = self.value
        for k in path:
            node = node[k]
        return node

    def add(self, path, value):
        # Non-replicating: perhaps put on own facet.
        node = self._node(path[:-1])
        if type(node) is list:
            node.insert(path[-1], copy(value))
        else:
            node[path[-1]] = value
        self.change_obs.changed()

    def change(self, path, old, value):
        # Non-replicating: perhaps put on own facet.
        node = self._node(path[:-1])
        key = path[-1]
        assert(node[key] == old)
        node[key] = copy(value)
        self.change_obs.changed()

    def delete(self, path, old):
        # Non-replicating: perhaps put on own facet.
        node = self._node(path[:-1])
        assert(node[path[-1]] == old)
        del node[path[-1]]
        self.change_obs.changed()

    def setAutoSave(self, value):
        self.auto_save = bool(value)
        self.save()

    def save(self):
        self.ref._set(self)

    def __str__(self):
        return str(self.value)

class AutoSave(object):
    def __init__(self, data, thread):
        self.data = data
        self.thread = thread
        self.clean = True

    def changed(self):
        if self.clean:
            self.clean = False
            self.thread.call(self.save)
    def save(self):
        self.data.save()
        self.clean = True
