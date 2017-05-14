from serf.publisher import Publisher
from serf.storage import save_fn
from serf.tables.table import Table, Key, FieldValue

class Collection(Table):
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
    serialize = ('#vat', '_primary', '_indices', '_pkey', '_subs')

    def __init__(self, storage, primary=None, indices=None, pkey=None, subs=None):
        Table.__init__(self, primary, indices, pkey, subs)
        self._storage = storage

    def add(self, item):
        """Adds an object to the collection."""
        info = item.getInfo()
        info['id'] = id = item.getId()
        info['sid'] = item.subscribe('*', self._onUpdate, (id,), persist=True)
        self.setKey(':id str', info)

    def discard(self, item):
        """Removes an object from the collection."""
        id = item.getId()
        kvs = self.pop(Key(':id str', id))
        for kv in kvs:
            item.unsubscribe('*', kv.value['sid'], persist=True)

    def get(self, query):
        """Returns the first object matching the query."""
        found = self.values(query)
        if found:
            return self._storage[found[0]['id']]

    def _onUpdate(self, ev, info, id):
        if ev == 'info':
            update = [FieldValue(':' + k, v) for k, v in info.iteritems()]
            self.update(Key(':id str', id), update)
