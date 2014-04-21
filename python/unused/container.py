"""Data containers: halfway to serialization."""

class Int(object):
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

class Text(object):
    def __init__(self, value):
        self.value = value if type(value) is unicode else value.decode('utf8')

    def get(self):
        return self.value

class Data(object):
    def __init__(self, value):
        self.value = value if type(value) is str else value.encode('utf8')

    def get(self):
        return self.value

class Cap(object):
    def __init__(self, cls, path):
        self.cls = cls
        self.path = path

class Ref(object):
    def __init__(self, root, path):
        self.root = root
        self.path = path
        self._cache = None

    def cache(self):
        if self._cache is None:
            ref = self.root
            for part in path.split('.'):
                ref = ref.get(part)
            self._cache = ref
        return self._cache

    def get(self):
        return self.cache().get()

AUTO_BOX = {
    int: Int,
    long: Int,
    unicode: Text,
    str: Data,
}

def box(value):
    try:
        box_method = value.box
    except AttributeError:
        return AUTO_BOX[type(value)](value)
    return box_method()

class Dict(object):
    def __init__(self, box=None):
        self.box = {} if box is None else box

    def __setitem__(self, key, value):
        self.box[key] = box(value)

    def get(self, key):
        if key is None:
            return self
        return self.box[key]


