"""Local reference to a vat slot."""

class RefError(Exception):
    pass

class Ref(object):
    def __init__(self, vat, path, facet=None):
        self._vat = vat
        self._path = path
        self._facet = facet
        if facet and facet.startswith('_'):
            raise RefError('Cannot make facet to private property')

    def _get(self):
        try:
            main = self._vat[self._path]
        except KeyError:
            raise RefError('No object in slot: ' + self._path)
        return getattr(main, self._facet) if self._facet else main

    def _set(self, value):
        if self._facet:
            raise RefError('Cannot set slot via a facet reference')
        self._vat[self._path] = value

    def _close(self):
        # Unclear if this should be allowed: if cache is weak-ref
        # then we shouldn't really need it.
        try:
            del self._vat.cache[self._path]
        except KeyError:
            pass

    def _erase(self):
        if self._facet:
            raise RefError('Cannot erase slot via a facet reference')
        self._close()
        try:
            del self._vat[self._path]
        except KeyError:
            pass

    def __getattr__(self, name):
        return getattr(self._get(), name)

    def __getitem__(self, key):
        return self._get()[key]

    def __setitem__(self, key, value):
        self._get()[key] = value

    def __delitem__(self, key):
        del self._get()[key]

    def __str__(self):
        return '/' + self._path + ('/' + self._facet if self._facet else '')

    def __repr__(self):
        return '~' + repr(self._vat[self._path]) + ' @ ' + self._path

    def __eq__(self, other):
        return type(other) is Ref and other._path == self._path and other._facet == self._facet

    def __ne__(self, other):
        return not self.__eq__(other)

    def _save(self, *_):
        if self._facet:
            raise RefError('Cannot save via a facet reference')
        self._vat.save(self._path)

    def _getFacet(self, facet):
        if self._facet:
            raise RefError('Cannot take facet of a facet')
        return Ref(self._vat, self._path, facet)
