"""Simple object to attach things to."""

class obj(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

def nop(*args):
    pass
