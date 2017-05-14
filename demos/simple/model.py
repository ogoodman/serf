import datetime
import os
from serf.fs_dict import FSDict
from serf.storage import Storage
from serf.util import dataRoot
from serf.publisher import Publisher
from serf.tables.collection import Collection

DATA_DIR = os.path.join(dataRoot(), 'client')

store = FSDict(DATA_DIR)
storage = Storage(store)

class Person(Publisher):
    serialize = ('name', 'age', '_subs')

    def __init__(self, name, age, subs=None):
        Publisher.__init__(self, subs)
        self.name = name
        self.age = age

    def haveBirthday(self):
        """Adds one to the age."""
        self.age += 1
        self.notify('info', {'age': self.age})
        self.notify('update', {'age': self.age})
        if hasattr(self, 'ref'):
            self.ref._save()

    def getId(self):
        """Get a unique object id."""
        return self.ref._path

    def getInfo(self):
        """Get brief details."""
        return {'age': self.age, 'name': self.name}

    def __repr__(self):
        return 'Person(%r,%r)' % (self.name, self.age)


class Subscriber(object):
    serialize = ()

    def onEvent(self, *args):
        print 'onEvent%r' % (args,)


def demo():
    storage['people'] = p = Collection(storage)

    storage['tom'] = t = Person('Tom', 3)
    storage['dick'] = d = Person('Dick', 4)
    storage['harry'] = h = Person('Harry', 4)

    p.add(t)
    p.add(d)
    p.add(h)

    del t, d, h, p

    p = storage['people']
    h = storage['harry']

    print p.values()

    h.haveBirthday()
    print p.values()

    print repr(storage['harry'])
    print storage['people'].values()

if __name__ == '__main__':
    demo()
