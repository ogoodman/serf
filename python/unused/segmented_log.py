"""Makes one big log file out of multiple segments."""

class SegmentedLog(object):
    def __init__(self, keyfn, dir):
        self.keyfn = keyfn # e.g. time.strftime('%Y%m%d')
        self.dir = dir
        self._chunks = self.dir.keys()
        self._chunks.sort()
        self._begin = {} # chunks -> begin values
        if self._chunks:
            last_key = self._chunks[-1]
            last = self.dir[last_key]
            self._begin[last_key] = last.begin()
            self._end = last.end()
        else:
            self._end = 0

    def begin(self, key=None):
        if key is None:
            if not self._chunks:
                return 0
            key = self._chunks[0]
        if key not in self._begin:
            self._begin[key] = self.dir[key].begin()
        return self._begin[key]

    def end(self):
        return self._end

    def append(self, item):
        key = self.keyfn() # typically a formatted date
        if not self._chunks or key > self._chunks[-1]:
            self._chunks.append(key)
            self.dir.addLogFile(key, self._end)
            self._begin[key] = self._end
        else:
            # In case dates are not monotone: e.g. user changes system
            # clock / timezone. Always append to highest dated chunk.
            key = self._chunks[-1]
        self.dir[key].append(item)
        self._end += 1

    def __getitem__(self, i):
        return self.dir[self.find(i)][i]

    def find(self, i):
        for key in reversed(self._chunks):
            if i >= self.begin(key):
                return key
        raise IndexError(i)

    def removeBefore(self, key):
        for i, k in enumerate(self._chunks):
            if k >= key:
                break
            del self.dir[k]
            if k in self._begin:
                del self._begin[k]
        del self._chunks[:i]
