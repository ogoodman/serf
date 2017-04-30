import datetime
import os
from serf.fs_dict import FSDict
from serf.storage import Storage
from serf.util import dataRoot

DATA_DIR = os.path.join(dataRoot(), 'client')

store = FSDict(DATA_DIR)
storage = Storage(store)

class Person(object):
    serialize = ('name', 'age', 'friends')

    def __init__(self, name, age, friends=None):
        self.name = name
        self.age = age
        self.friends = friends or []

    def getName(self):
        return self.name
    def getAge(self):
        return self.age
    def getFriends(self):
        return self.friends

    def addFriend(self, friend):
        self.friends.append(friend)
    def haveBirthday(self):
        self.age += 1

    def __repr__(self):
        return 'Person(%r,%r,%r)' % (self.name, self.age, self.friends)
