from serf.tables.table import *
from serf.tables.table_handle import TableHandle

class Login(object):
    """The Login capability requires/creates a 'users' table in storage."""

    serialize = ('_vat',)

    def __init__(self, vat):
        self._vat = vat
        if 'users' not in self._vat:
            self._vat['users'] = Table()

    def _get_rec(self, userid):
        users = TableHandle(self._vat['users'])
        user_recs = users.values(Key(':userid str', userid))
        if not user_recs:
            return None
        return user_recs[0]

    def _check(self, userid, password):
        user_rec = self._get_rec(userid)
        if user_rec is None:
            return False
        return password == user_rec['password']

    def login(self, userid, password):
        """Checks user and password match and return a user object.

        If there is no match, None is returned.
        """
        user_rec = self._get_rec(userid)
        if user_rec is None:
            #print 'No such user:', userid
            return None
        if password != user_rec['password']:
            #print 'Incorrect password given for:', userid
            return None
        oid = user_rec['oid']
        return self._vat[oid]

    def changePassword(self, userid, oldpw, newpw):
        """Allows a user to change their password."""
        if not self._check(userid, oldpw):
            return False
        self._vat['users'].update(Key(':userid str', userid), [FieldValue(':password', newpw)])
        return True
