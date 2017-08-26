from collection import Collection
from serf.model import Model

class CollectionModel(Model, Collection):
    serialize = ('#vat', 'data', '_subs', '_table')

    def __init__(self, storage, data=None, subs=None, table=None):
        Collection.__init__(self, storage, table)
        Model.__init__(self, data, subs)

    def addSub(self, sub):
        Collection.addSub(self, sub)
        Model.addSub(self, sub)

    def removeSub(self, sub):
        Collection.removeSub(self, sub)
        Model.removeSub(self, sub)

    def get(self, key):
        if type(key) in (int, long):
            return Collection.get(self, key)
        return Model.get(self, key)

    def update(self, values, *args, **kw):
        if type(values) is dict and args == () and kw == {}:
            return Model.update(self, values)
        return Collection.update(self, values, *args, **kw)
