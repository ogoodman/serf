"""Classes representing the parsed contents of a serf IDL file."""

from serf.util import EqualityMixin

TYPES = ['void', 'bool', 'byte', 'int', 'long', 'float', 'ascii', 'text', 'data', 'list', 'dict', 'time', 'var', 'future']

COMPOUND = ['list', 'dict', 'future']

class IDLType(EqualityMixin):
    """Represents an IDL static type."""
    def __init__(self, name, elem_type=None, opt=False):
        """Make an IDL type object.

        The name must be one of the primitive or compound types in TYPES.
        If name is one of the compound types, 'list' or 'dict' then an
        elem_type must be provided as well which must be another IDLType
        instance.

        If IDLType represents an argument type it may be marked as
        optional.
        """
        if name not in TYPES:
            raise Exception('unexpected type: %r' % name)
        if elem_type is not None:
            assert(name in COMPOUND)
        self.name = name
        self.elem_type = elem_type
        self.opt = opt

    def __repr__(self):
        if self.elem_type is None:
            return "IDLType('%s')" % self.name
        return "IDLType('%s', %s)" % (self.name, self.elem_type)

class ProxyType(EqualityMixin):
    """Represents a Proxy."""
    def __init__(self, type_name, opt=False):
        self.name = 'proxy'
        self.type_name = type_name
        self.opt = opt

    def __repr__(self):
        return "ProxyType('%s')" % self.type_name

class Member(object):
    """Represents a struct or exception member."""
    def __init__(self, type, name):
        self.type = type
        self.name = name

    def __repr__(self):
        return 'Member(%r,%r)' % (self.type, self.name)

class InterfaceDef(object):
    """Represents an interface definition."""
    def __init__(self, cls, method_list):
        self.cls = cls
        self.method_list = method_list

class ExceptionDef(object):
    """Represents an exception definition."""
    def __init__(self, cls, member_list):
        self.cls = cls
        self.member_list = member_list

    def __repr__(self):
        return 'ExceptionDef(%r, %r)' % (self.cls, self.member_list)
