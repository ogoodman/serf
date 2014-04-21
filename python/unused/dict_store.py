"""Mock persistent storage, using a dictionary."""

class DictStore(object):
    def __init__(self):
        self.value = {}

    def put(self, value):
        self.value = value

    def get(self):
        return dict(self.value)

    def folder(self, path):
        if path not in self.value:
            self.value[path] = DictStore()
        return self.value[path]
