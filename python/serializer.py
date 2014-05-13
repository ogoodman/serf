"""A serializer.

The main exported functions are encode and decode which write 
(resp. read) serializable data to (resp. from) a file-like object.
Variants encodes and decodes are also provided which return 
(resp. accept) string encodings.

Custom encodings and decodings may be enabled by passing an
optional context object. It has three methods:

ctx.custom(type_name, value)
    Called when decoding a record, this may return a value for it. 
    If it returns None, a Record instance is produced.

ctx.codec(type_id)
    Called when decoding a message, this must return a codec and
    a type name. The codec is used to decode the message data and
    ctx.custom is then called to allow a custom value to be
    generated. If None is returned, a Record is produced.

ctx.record(any)
    Called when encoding encounters a non built-in serializable
    type. It must return a type_name, value pair which is then
    treated as a Record for encoding purposes. If it cannot do so
    it should raise a SerializationError.

ctx.namedCodec(type_name)
    Called when encoding a Record, this may return a codec and a
    type id, in which case a message is produced. If it returns
    None, None then a record is produced using the type_name
    and the default encoder.
"""

import datetime
import struct
from cStringIO import StringIO

POD_TYPES = [type(None), bool, int, long, str, unicode, float, list, dict, tuple]

class SerializationError(Exception):
    pass

class Codec(object):
    def decodeType(self, f, ctx):
        return self
    def encodeType(self, f):
        f.write(self.type_byte)

class NoneCodec(Codec):
    type_byte = '-'
    def decode(self, f, ctx):
        return None
    def encode(self, f, value, ctx):
        pass
NULL = NoneCodec()

class BoolCodec(Codec):
    type_byte = 'b'
    def decode(self, f, ctx):
        return f.read(1) != '\x00'
    def encode(self, f, value, ctx):
        f.write('\x01' if value else '\x00')
BOOL = BoolCodec()

class IntCodec(Codec):
    def __init__(self, width, format, type_byte):
        self.width = width
        self.format = format
        self.type_byte = type_byte
    def decode(self, f, ctx):
        return struct.unpack(self.format, f.read(self.width))[0]
    def encode(self, f, value, ctx):
        f.write(struct.pack(self.format, value))

BYTE  = IntCodec(1, '>B', 'B')
INT16 = IntCodec(2, '>h', 'h')
INT32 = IntCodec(4, '>i', 'i')
INT64 = IntCodec(8, '>q', 'q')
FLOAT = IntCodec(8, '>d', 'd') 

class StrCodec(Codec):
    def __init__(self, type_byte, len_type=INT32):
        self.type_byte = type_byte
        self.len_type = len_type
    def decode(self, f, ctx):
        n = self.len_type.decode(f, ctx)
        return f.read(n)
    def encode(self, f, value, ctx):
        self.len_type.encode(f, len(value), ctx)
        f.write(value)

DATA = StrCodec('r')
TOKEN = StrCodec('k', len_type=INT16)
ASCII = StrCodec('a')

class TextCodec(Codec):
    type_byte = 'u'
    def decode(self, f, ctx):
        n = INT32.decode(f, ctx)
        return f.read(n).decode('utf8')
    def encode(self, f, value, ctx):
        data = value.encode('utf8')
        INT32.encode(f, len(data), ctx)
        f.write(data)
TEXT = TextCodec()

EPOCH_BEGIN = datetime.datetime(1970, 1, 1)
SEC_PER_DAY = 3600 * 24

def toEpochUSec(dt):
    t = dt - EPOCH_BEGIN
    return (t.days * SEC_PER_DAY + t.seconds) * 1000000 + t.microseconds

def toDateTime(t):
    return EPOCH_BEGIN + datetime.timedelta(microseconds=t)

class TimeCodec(Codec):
    type_byte = 't'
    def decode(self, f, ctx):
        return toDateTime(INT64.decode(f, ctx))
    def encode(self, f, value, ctx):
        INT64.encode(f, toEpochUSec(value), ctx)
TIME = TimeCodec()

class AnyCodec(Codec):
    type_byte = 'A'
    def decode(self, f, ctx):
        return decode(f, ctx)
    def encode(self, f, value, ctx):
        encode(f, value, ctx)
ANY = AnyCodec()

class Record(object):
    def __init__(self, type_name, value, type_id=0, codec=None):
        self.type_name = type_name
        self.value = value
        self.type_id = type_id
        self.codec = codec
    def __eq__(self, other):
        if type(other) is type(self):
            return (self.type_name,self.value) == (other.type_name,other.value)
        return False
    def __str__(self):
        return '%s(%r)' % (self.type_name, self.value)

class RecordCodec(Codec):
    type_byte = 'R'
    def decode(self, f, ctx):
        name = TOKEN.decode(f, ctx)
        body = ANY.decode(f, ctx)
        if ctx is not None:
            result = ctx.custom(name, body)
            if result is not None:
                return result
        return Record(name, body)
RECORD = RecordCodec()

class MessageCodec(Codec):
    type_byte = '@'
    def decode(self, f, ctx):
        type_id = INT32.decode(f, ctx)
        tmp = StringIO(DATA.decode(f, ctx))
        codec = None
        if ctx is not None:
            codec, type_name = ctx.codec(type_id)
        if codec is None:
            return Record('@', tmp.getvalue(), type_id)
        value = codec.decode(tmp, ctx)
        result = ctx.custom(type_name, value)
        if result is not None:
            return result
        return Record(type_name, value, type_id, codec)
MESSAGE = MessageCodec()

class TypeCodec(Codec):
    type_byte = 'Y'
    def encode(self, f, value, ctx):
        value.encodeType(f)
    def decode(self, f, ctx):
        factory = DECODER[f.read(1)]
        return factory.decodeType(f, ctx)

TYPE = TypeCodec()

class ARRAY(Codec):
    type_byte = 'L'
    def __init__(self, item_codec):
        self.item_codec = item_codec
    def decode(self, f, ctx):
        n = INT32.decode(f, ctx)
        return [self.item_codec.decode(f, ctx) for i in xrange(n)]
    def encode(self, f, value, ctx):
        INT32.encode(f, len(value), ctx)
        for v in value:
            self.item_codec.encode(f, v, ctx)
    def encodeType(self, f):
        f.write(self.type_byte)
        self.item_codec.encodeType(f)
    @staticmethod
    def decodeType(f, ctx):
        item_codec = TYPE.decode(f, ctx)
        return ARRAY(item_codec)
LIST = ARRAY(ANY)

class TUPLE(Codec):
    type_byte = 'T'
    def __init__(self, *codecs):
        self.codecs = codecs
    def decode(self, f, ctx):
        return [c.decode(f, ctx) for c in self.codecs]
    def encode(self, f, value, ctx):
        for c, v in zip(self.codecs, value):
            c.encode(f, v, ctx)
    def encodeType(self, f):
        f.write(self.type_byte)
        INT32.encode(f, len(self.codecs), None)
        for c in self.codecs:
            c.encodeType(f)
    @staticmethod
    def decodeType(f, ctx):
        n = INT32.decode(f, ctx)
        return TUPLE(*[TYPE.decode(f, ctx) for i in xrange(n)])

class VECTOR(Codec):
    type_byte = 'V'
    def __init__(self, item_codec, size):
        self.item_codec = item_codec
        self.size = size
    def decode(self, f, ctx):
        return [self.item_codec.decode(f, ctx) for i in xrange(self.size)]
    def encode(self, f, value, ctx):
        assert(len(value) == self.size)
        for v in value:
            self.item_codec.encode(f, v, ctx)
    def encodeType(self, f):
        f.write(self.type_byte)
        self.item_codec.encodeType(f)
        INT32.encode(f, self.size, None)
    @staticmethod
    def decodeType(f, ctx):
        item_codec = TYPE.decode(f, ctx)
        n = INT32.decode(f, ctx)
        return VECTOR(item_codec, n)

class MAP(Codec):
    type_byte = 'M'
    def __init__(self, key_type, value_type):
        self.key_type = key_type
        self.value_type = value_type
    def decode(self, f, ctx):
        value = {}
        n = INT32.decode(f, ctx)
        for i in xrange(n):
            k = self.key_type.decode(f, ctx)
            value[k] = self.value_type.decode(f, ctx)
        return value
    def encode(self, f, value, ctx):
        INT32.encode(f, len(value), ctx)
        for k, v in value.iteritems():
            self.key_type.encode(f, k, ctx)
            self.value_type.encode(f, v, ctx)
    def encodeType(self, f):
        f.write(self.type_byte)
        self.key_type.encodeType(f)
        self.value_type.encodeType(f)
    @staticmethod
    def decodeType(f, ctx):
        key_type = TYPE.decode(f, ctx)
        value_type = TYPE.decode(f, ctx)
        return MAP(key_type, value_type)
DICT = MAP(TOKEN, ANY)

FIELD_SPEC = ARRAY(TUPLE(TOKEN, TYPE))

class STRUCT(Codec):
    type_byte = 'S'
    def __init__(self, fields):
        self.fields = fields # [[key, type],...]
    def decode(self, f, ctx):
        value = {}
        for k, c in self.fields:
            value[k] = c.decode(f, ctx)
        return value
    def encode(self, f, value, ctx):
        for k, c in self.fields:
            c.encode(f, value[k], ctx)
    def encodeType(self, f):
        f.write(self.type_byte)
        FIELD_SPEC.encode(f, self.fields, None)
    @staticmethod
    def decodeType(f, ctx):
        return STRUCT(FIELD_SPEC.decode(f, ctx))

class CONST(Codec):
    type_byte = 'C'
    def __init__(self, value):
        self.value = value
    def decode(self, f, ctx):
        return self.value
    def encode(self, f, value, ctx):
        pass
    def encodeType(self, f):
        f.write(self.type_byte)
        ANY.encode(f, self.value, None)
    @staticmethod
    def decodeType(f, ctx):
        return CONST(ANY.decode(f, ctx))

ENUM_DICT = MAP(TOKEN, INT16)

class ENUM(Codec):
    type_byte = 'E'
    def __init__(self, k_to_int):
        self.k_to_int = k_to_int
        self.int_to_k = {}
        for k, i in k_to_int.iteritems():
            self.int_to_k[i] = k
    def encodeType(self, f):
        f.write(self.type_byte)
        ENUM_DICT.encode(f, self.k_to_int, None)
    @staticmethod
    def decodeType(f, ctx):
        return ENUM(ENUM_DICT.decode(f, ctx))
    def encode(self, f, value, ctx):
        INT16.encode(f, self.k_to_int[value], ctx)
    def decode(self, f, ctx):
        return self.int_to_k[INT16.decode(f, ctx)]

def fallbackEncode(f, value, ctx):
    """Provides encoding for Records and all custom serializables."""

    # If not a record, try to convert it to one.
    if type(value) is not Record:
        try:
            value = ctx.record(value)
            assert(type(value) is Record)
        except:
            raise SerializationError(value.__class__.__name__)

    # If it is an opaque message holder, write it out.
    type_name, body = value.type_name, value.value
    if type_name == '@':
        f.write('@')
        INT32.encode(f, value.type_id, ctx)
        DATA.encode(f, body, ctx)
        return

    # Check if there is a registered codec for this type_name.
    if ctx is None:
        codec = None
    else:
        codec, type_id = ctx.namedCodec(type_name)

    if codec is None:
        f.write('R')
        TOKEN.encode(f, type_name, ctx)
        ANY.encode(f, body, ctx)
    else:
        f.write('@')
        INT32.encode(f, type_id, ctx)
        tmp = StringIO()
        codec.encode(tmp, body, ctx)
        DATA.encode(f, tmp.getvalue(), ctx)

class Registry(object):
    """Provides a usable implementation of the context interface."""
    def __init__(self):
        self.by_name = {}
        self.by_id = {}
        self.custom_by_name = {}
    def register(self, name, id, codec):
        self.by_name[name] = (codec, id)
        self.by_id[id] = (codec, name)
    def addCustom(self, name, factory):
        self.custom_by_name[name] = factory

    def codec(self, id):
        return self.by_id[id]
    def namedCodec(self, name):
        return self.by_name[name]
    def custom(self, name, value):
        try:
            factory = self.custom_by_name[name]
        except KeyError:
            return None
        return factory(value)
    def record(self, any):
        name, value = any.get_state()
        return Record(name, value)

DECODER = {}
ENCODER = {}

def register(factory, type_byte=None):
    DECODER[type_byte or factory.type_byte] = factory

def encode(f, value, ctx=None, encoder=None):
    if encoder is None:
        if type(value) in ENCODER:
            encoder = ENCODER[type(value)](value)
        elif isinstance(value, Codec):
            encoder = TYPE
        else:
            return fallbackEncode(f, value, ctx)
    encoder.encodeType(f)
    encoder.encode(f, value, ctx)

def decode(f, ctx=None):
    codec = TYPE.decode(f, ctx)
    return codec.decode(f, ctx)

def encodes(value, ctx=None, encoder=None):
    f = StringIO()
    encode(f, value, ctx, encoder)
    return f.getvalue()

def decodes(s, ctx=None, check=True):
    f = StringIO(s)
    value = decode(f, ctx)
    if check:
        assert(f.read() == '')
    return value

register(NULL)  # -
register(BOOL)  # b

register(BYTE)  # B
register(INT16) # h
register(INT32) # i
register(INT64) # q
register(FLOAT) # d

register(DATA)  # r
register(ASCII) # a
register(TEXT)  # u
register(TOKEN) # k

register(TIME)  # t

register(ANY)     # A
register(RECORD)  # R
register(MESSAGE) # @
register(TYPE)    # Y

register(ARRAY)  # L
register(TUPLE)  # T
register(VECTOR) # V
register(MAP)    # M
register(STRUCT) # S
register(CONST)  # C

def findIntEncoder(value):
    if -2147483648 <= value <= 2147483647:
        return INT32
    return INT64
def findStringEncoder(value):
    try:
        value.decode('ascii') # will succeed if ascii
        return ASCII
    except UnicodeDecodeError:
        return DATA

ENCODER[type(None)] = lambda v: NULL
ENCODER[bool] = lambda v: BOOL
ENCODER[int] = findIntEncoder
ENCODER[long] = findIntEncoder
ENCODER[float] = lambda v: FLOAT
ENCODER[list] = lambda v: LIST
ENCODER[tuple] = lambda v: LIST
ENCODER[str] = findStringEncoder
ENCODER[unicode] = lambda v: TEXT
ENCODER[dict] = lambda v: DICT
ENCODER[datetime.datetime] = lambda v: TIME
