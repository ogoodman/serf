"""Simple capability for use in tests."""

class Person(object):
    serialize = ('env',)

    def __init__(self, env):
        self.env = env

    def haveBirthday(self):
        self.env['age'] += 1

    def description(self):
        return '%s age %s' % (self.env['name'], self.env['age'])

    def dadsName(self):
        return self.env['dad']['name']

    def whatTime(self):
        return self.env['time'].time()
