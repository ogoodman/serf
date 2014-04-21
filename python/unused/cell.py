"""Something which holds a value."""

class Cell(object):
    def __init__(self, value=None):
        self.value = value

    def put(self, value):
        self.value = value

    def get(self):
        return self.value
