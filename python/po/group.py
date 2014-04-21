"""Proxy for a collection of references, all of which receive the call."""

import sys, traceback

def isSerializable(obj):
    if type(getattr(obj, 'serialize', None)) is tuple:
        return True
    return type(obj).__name__ in ('Ref', 'Proxy')

class Group(object):
    serialize = ('group',)

    def __init__(self, group=None, fatal=None, errh=None, obs=None):
        """Make group of objects which are all called when this is.

        group: initial set of references
        fatal: exceptions s.t. member is removed if any of these are thrown.
        errh: called with (member, name, args, exception) on error, if set.
        """
        self._group = [] if group is None else group
        self._fatal = [] if fatal is None else fatal
        self._errh = errh
        self._obs = NullObs() if obs is None else obs

    @property
    def group(self):
        return [o for o in self._group if isSerializable(o)]

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        def _call(*args, **kw):
            eh_exc = None
            # copy self.group because the calls may change group,
            # or yield allowing something else to change it.
            for m in list(self._group):
                try:
                    getattr(m, name)(*args, **kw)
                except Exception, e:
                    handled = False
                    if self._errh is not None:
                        try:
                            self._errh(m, name, args, e)
                            handled = True
                        except Exception, eh_exc:
                            pass
                    # FIXME: do fatal first, then errh?
                    for f in self._fatal:
                        if isinstance(e, f):
                            self._remove(m)
                            break
                    else:
                        if not handled:
                            traceback.print_exc()
                            print >>sys.stderr, 'In Group._call %r.%s %s %s' % (m, name, args, kw)
            if eh_exc is not None:
                raise eh_exc
        return _call

    def _add(self, m):
        if m not in self._group:
            self._group.append(m)
            self._obs.changed()

    def _remove(self, m):
        try:
            self._group.remove(m)
        except ValueError:
            pass
        else:
            self._obs.changed()

    def __nonzero__(self):
        return bool(self._group)

class NullObs(object):
    def changed(self):
        pass
