from publisher import Publisher

class Model(Publisher):
    def __init__(self):
        Publisher.__init__(self)
        self.values = {}
    def get(self, key):
        return self.values.get(key)
    def set(self, key, value):
        old = self.values.get(key)
        self.values[key] = value
        if value != old:
            self.notify('change', {'key':key, 'old':old, 'new':value})
