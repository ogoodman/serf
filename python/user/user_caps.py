"""A simple dictionary of caps."""

class UserCaps(object):
    serialize = ('_caps',)

    def __init__(self, caps):
        self._caps = caps

    def _save(self):
        pass

    def __getitem__(self, name):
        return self._caps[name]

    def __setitem__(self, name, value):
        self._caps[name] = value
        self._save()

    def __delitem__(self, name):
        del self._caps[name]
        self._save()

    def keys(self):
        return self._caps.keys()
