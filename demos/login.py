from serf.tables.table import *
from serf.tables.table_handle import TableHandle

class Login(object):
    """The Login capability requires/creates a 'users' table in storage."""

    serialize = ('_vat',)

    def __init__(self, vat):
        self.vat = vat

    def login(self, userid, password):
        """Checks user and password match and return a user object.

        If there is no match, None is returned.
        """
        if 'users' not in self.vat:
            self.vat['users'] = Table()
        users = TableHandle(self.vat['users'])
        user_recs = users.values(Key(':userid str', userid))
        if not user_recs:
            print 'No such user:', userid
            return None
        user_rec = user_recs[0]
        if password != user_rec['password']:
            print 'Incorrect password given for:', userid
            return None
        oid = user_rec['oid']
        obj = self.vat[oid]
        return obj
