from serf.publisher import Publisher, SubscribeMixin, PERSISTENT
from serf.storage import save_fn
from serf.tables.table import Table, Key, FieldValue

class Collection(SubscribeMixin):
    """Table of brief info for a set of persistent objects.

    Objects must implement getId() returning a unique identifier, and
    getInfo() returning a dict of brief info for the object. They must
    also be Publishers with an 'info' event notifying of any changes
    to the info as a dict of modified key-value pairs.

    Info for objects added to the collection will remain up-to-date at
    all times.

    It can be used when we want to find objects by querying over
    properties, but don't want to have to instantiate all the objects
    in order to do so.
    """
    serialize = ('#vat', '_table')
    _version = 1

    def __init__(self, storage, table=None):
        self._table = Table() if table is None else table
        self._storage = storage

    def add(self, item):
        """Adds an object to the collection."""
        info = item.getInfo()
        info['id'] = id = item.getId()
        info['sid'] = item.subscribe('*', self._onUpdate, (id,), how=PERSISTENT)
        self._table.setKey(':id str', info)

    def discard(self, item):
        """Removes an object from the collection."""
        id = item.getId()
        kvs = self._table.pop(Key(':id str', id))
        for kv in kvs:
            item.unsubscribe('*', kv.value['sid'], how=PERSISTENT)

    def open(self, query):
        """Returns the first object matching the query."""
        found = self._table.values(query)
        if found:
            return self._storage[found[0]['id']]

    def addSub(self, sub):
        self._table.addSub(sub)

    def removeSub(self, sub):
        self._table.removeSub(sub)

    def select(self, filter=None):
        return self._table.select(filter)

    def pkeys(self, filter=None):
        return self._table.pkeys(filter)

    def values(self, filter=None):
        return self._table.values(filter)

    def count(self, filter=None):
        return self._table.count(filter)

    def maxPK(self):
        return self._table.maxPK()

    def update(self, filter, values, model=None):
        return self._table.update(filter, values, model)

    def get(self, pkey):
        return self._table.get(pkey)

    # TODO: updateIter, remove
    # NOTE: remove will have to unsubscribe like discard.

    def _onUpdate(self, ev, info, id):
        if ev == 'info':
            update = [FieldValue(':' + k, v) for k, v in info.iteritems()]
            self._table.update(Key(':id str', id), update)
