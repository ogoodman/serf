"""Type checking and normalization."""

from datetime import date
from fred.obj import obj

def normalize_str(value):
    if not isinstance(value, basestring):
        raise TypeError('type of %r is not basestring' % value)
    if type(value) is unicode:
        return value
    # might fail I guess if type is something fancy.
    return value.decode('utf8')

def normalize_date(value):
    if type(value) is not date:
        raise TypeError('type of %r is not datetime.date' % value)
    return value

def normalize_int(value):
    if type(value) not in (int, long):
        raise TypeError('type of %r is not integer' % value)
    return value

NORMALIZERS = {
    'str': normalize_str,
    'date': normalize_date,
    'int': normalize_int,
}

def Types(env=None):
    def normalize(value, typ):
        try:
            nfunc = NORMALIZERS[typ]
        except KeyError:
            raise ValueError('unknown type %r' % typ)
        return nfunc(value)

    def denormalize(value, typ):
        if typ not in NORMALIZERS:
            raise ValueError('unknown type %r' % typ)
        return value

    return obj(types=obj(normalize=normalize, denormalize=denormalize))


def RefTypes(env):
    types = Types().types

    def normalize_ref(value):
        if not env.proxy_factory.isProxy(value):
            raise TypeError('%r is not a proxy' % value)
        return env.proxy_factory.toSProxy(value)

    def normalize(value, typ):
        if typ == 'ref' and hasattr(env, 'proxy_factory'):
            return normalize_ref(value)
        return types.normalize(value, typ)

    def denormalize_ref(value):
        if not env.proxy_factory.isSProxy(value):
            raise TypeError('%r is not a serializable proxy' % value)
        return env.proxy_factory.toProxy(value)

    def denormalize(value, typ):
        if typ == 'ref' and hasattr(env, 'proxy_factory'):
            return denormalize_ref(value)
        return types.denormalize(value, typ)

    return obj(types=obj(normalize=normalize, denormalize=denormalize))
