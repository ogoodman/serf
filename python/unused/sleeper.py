"""Demo object which blocks a system thread by sleeping."""

import time

class Sleeper(object):
    serialize = ()

    def sleep(self, t=1):
        time.sleep(1)
