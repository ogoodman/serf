"""Opaque handle for making remote calls."""

class Proxy(object):
    def __init__(self, node, path, vat=None):
        self._node = node
        self._path = path
        self._vat = vat

    def __getattr__(self, method):
        if method.startswith('_'):
            raise AttributeError(method)
        if method.endswith('_f'):
            return self._getattr_f(method[:-2])
        return self._getattr(method)

    def _getattr(self, method):
        def _mcall(*args):
            cb = self._vat.call(self._node, self._path, method, args)
            return cb.wait()
        return _mcall

    def _getattr_f(self, method):
        def _mcall_f(*args):
            return self._vat.call(self._node, self._path, method, args)
        return _mcall_f

    def __getitem__(self, key):
        return self._getattr('__getitem__')(key)

    def __setitem__(self, key, value):
        self._getattr('__setitem__')(key, value)

    def __delitem__(self, key):
        self._getattr('__delitem__')(key)

    def __str__(self):
        return 'serf://' + self._node + '/' + self._path

    def __eq__(self, other):
        return (type(other) is Proxy and
                other._node == self._node and
                other._path == self._path)

    def __ne__(self, other):
        return not self.__eq__(other)
