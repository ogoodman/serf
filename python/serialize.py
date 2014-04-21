"""Serialization for simple structures."""

import struct
from cStringIO import StringIO

POD_TYPES = [type(None), bool, int, long, str, unicode, float, list, dict, tuple]

INT32_MIN = -2**31
INT32_MAX = 2**31-1

class SerializationError(Exception):
    pass

class SNone(object):
    def encode(self, f, value, ctx, lev):
        f.write(struct.pack('>b', 0))
    def decode(self, f, ctx, lev):
        return None

class SBool(object):
    def encode(self, f, value, ctx, lev):
        f.write(struct.pack('>bb', 1, int(value)))
    def decode(self, f, ctx, lev):
        return bool(struct.unpack('>b', f.read(1))[0])

class Int32(object):
    def decode(self, f, ctx, lev):
        return struct.unpack('>i', f.read(4))[0]

class Int64(object):
    def decode(self, f, ctx, lev):
        return struct.unpack('>q', f.read(8))[0]

class Int(object):
    def encode(self, f, value, ctx, lev):
        if INT32_MIN <= value <= INT32_MAX:
            f.write(struct.pack('>bi', 2, value))
        else:
            f.write(struct.pack('>bq', 3, value))

class Data(object):
    def encode(self, f, value, ctx, lev):
        f.write(struct.pack('>bI', 4, len(value)))
        f.write(value)
    def decode(self, f, ctx, lev):
        n = struct.unpack('>I', f.read(4))[0]
        return f.read(n)

class Text(object):
    def encode(self, f, value, ctx, lev):
        data = value.encode('utf8')
        f.write(struct.pack('>bI', 5, len(data)))
        f.write(data)
    def decode(self, f, ctx, lev):
        n = struct.unpack('>I', f.read(4))[0]
        return f.read(n).decode('utf8')

class List(object):
    def encode(self, f, value, ctx, lev):
        f.write(struct.pack('>bI', 6, len(value)))
        lev += 1
        for v in value:
            encode(f, v, ctx, lev)
    def decode(self, f, ctx, lev):
        lev += 1
        n = struct.unpack('>I', f.read(4))[0]
        return [decode(f, ctx, lev) for i in xrange(n)]

class Tuple(object):
    def encode(self, f, value, ctx, lev):
        lev += 1
        f.write(struct.pack('>bI', 7, len(value)))
        for v in value:
            encode(f, v, ctx, lev)
    def decode(self, f, ctx, lev):
        lev += 1
        n = struct.unpack('>I', f.read(4))[0]
        return tuple([decode(f, ctx, lev) for i in xrange(n)])

class Dict(object):
    def encode(self, f, value, ctx, lev):
        lev += 1
        f.write(struct.pack('>bI', 8, len(value)))
        for k, v in value.iteritems():
            assert(len(k) < 256)
            f.write(struct.pack('>B', len(k)))
            f.write(k)
            encode(f, v, ctx, lev)
    def decode(self, f, ctx, lev):
        lev += 1
        n = struct.unpack('>I', f.read(4))[0]
        result = {}
        for i in xrange(n):
            klen = struct.unpack('>B', f.read(1))[0]
            k = f.read(klen)
            v = decode(f, ctx, lev)
            result[k] = v
        return result

class Float(object):
    def encode(self, f, value, ctx, lev):
        f.write(struct.pack('>bd', 9, value))
    def decode(self, f, ctx, lev):
        return struct.unpack('>d', f.read(8))[0]

class RecordType(object):
    def encode(self, f, value, ctx, lev):
        lev += 1
        if ctx is None:
            raise SerializationError('No context provided for encoding data of type %s' % type(value))
        name, data = ctx(value, lev)
        f.write('\x0A')
        encode(f, name, ctx, lev)
        encode(f, data, ctx, lev)

    def decode(self, f, ctx, lev):
        lev += 1
        name = decode(f, ctx, lev)
        data = decode(f, ctx, lev)
        if ctx is None:
            raise SerializationError('No context provided for decoding record of type %s' % name)
        return ctx(name, data, lev)

DECODER = {
    0: SNone(),
    1: SBool(),
    2: Int32(),
    3: Int64(),
    4: Data(), # str / binary
    5: Text(), # unicode
    6: List(), # mixed types
    7: Tuple(),
    8: Dict(), # string keys
    9: Float(),
    10: RecordType(),
    }

ENCODER = {
    type(None): SNone(),
    bool: SBool(),
    int: Int(),
    long: Int(),
    str: Data(), # str / binary
    unicode: Text(), # unicode
    list: List(), # mixed types
    tuple: Tuple(), # mixed types
    dict: Dict(), # string keys up to 255 chars.
    float: Float(),
}

RECORD_ENCODER = RecordType()

class Record(object):
    def __init__(self, name, data, lev=0):
        self.name = name
        self.data = data
        self.lev = lev

    def __repr__(self):
        if self.name == 'inst' and 'CLS' in self.data:
            d = dict(self.data)
            cls = d.pop('CLS')
            indent = '  ' * self.lev
            args = (',\n%s  ' % indent).join(['%s=%r' % (k, v) for k, v in d.iteritems()])
            opt_nl = '\n%s  ' % indent if len(d) > 1 else ''
            return '%s(%s%s)' % (cls, opt_nl, args)
        return '%s(%s)' % (self.name, self.data)

def encode(f, value, ctx=None, lev=0):
    encoder = ENCODER.get(type(value), RECORD_ENCODER)
    encoder.encode(f, value, ctx, lev)

def decode(f, ctx=None, lev=0):
    return DECODER[struct.unpack('>b', f.read(1))[0]].decode(f, ctx, lev)

def encodes(value, ctx=None):
    f = StringIO()
    encode(f, value, ctx)
    return f.getvalue()

def decodes(s, ctx=Record, check=True):
    f = StringIO(s)
    value = decode(f, ctx)
    if check:
        assert(f.read() == '')
    return value
