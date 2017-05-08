"""Admin cap which can add users."""

from serf.util import randomString
from serf.tables.table import *
from serf.tables.table_handle import TableHandle

from user_caps import UserCaps

class Admin(object):
    """Admin cap which can add users."""

    serialize = ('#vat',)

    def __init__(self, vat):
        self._vat = vat

    def userTable(self):
        if 'users' not in self._vat:
            self._vat['users'] = Table()
        return TableHandle(self._vat['users'])

    def addUser(self, userid, password):
        users = self.userTable()
        user_recs = users.values(Key(':userid str', userid))
        if user_recs:
            raise Exception('User: %s already exists' % userid)
        path = 'caps/' + randomString(12)
        self._vat[path] = UserCaps({})
        user_rec = dict(userid=userid, password=password, oid=path)
        users.insert(user_rec)
        return self._vat[path]

