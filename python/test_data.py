"""Simple demo of master-slave switching."""

from fred.obj import obj

class TestData(object):
    serialize = ('value', 'is_master')

    def __init__(self, value=None, master=False):
        self.value = value
        self.is_master = master
        self.master = obj(get=self.get, set=self.set)
        self.slave = obj(get=self.get)
        self.public = self.master if master else self.slave

    def get(self):
        return self.value

    def set(self, value):
        self.value = value

    def setMaster(self, be_master):
        self.is_master = be_master
        self.public = self.master if be_master else self.slave

    def isMaster(self):
        return self.is_master

    def doSet(self, v):
        self.value.set(v) # Assumes v is ref or instance w/set method.
