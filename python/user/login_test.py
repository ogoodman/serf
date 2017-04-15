import unittest
from login import Login
from admin import Admin

class LoginTest(unittest.TestCase):
    def test(self):
        storage = {}
        a = Admin(storage)
        l = Login(storage)

        a.addUser('fred', 's3cr3t')
        u = l.login('fred', 's3cr3t')
        self.assertTrue(u is not None)

        u2 = l.login('fred', 's3cr3t')
        self.assertTrue(u is u2)

        u3 = l.login('fred', 'password')
        self.assertTrue(u3 is None)

if __name__ == '__main__':
    unittest.main()
