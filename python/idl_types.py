"""Classes representing the parsed contents of a serf IDL file."""

TYPES = ['void', 'bool', 'byte', 'int', 'long', 'float', 'ascii', 'text', 'data', 'list', 'dict', 'time', 'var', 'future']

COMPOUND = ['list', 'dict', 'future']

BY_CREF = COMPOUND + ['ascii', 'text', 'data', 'var']

CPP_TYPE = {
    'void': 'void',
    'bool': 'bool',
    'byte': 'serf::byte',
    'int': 'int32_t',
    'long': 'int64_t',
    'float': 'double',
    'ascii': 'std::string',
    'text': 'std::string',
    'data': 'std::string',
    'list': 'std::vector<%s>',
    'dict': 'std::map<std::string, %s>',
    'time': 'boost::posix_time::ptime',
    'var': 'serf::Var',
    'future': 'serf::Future<%s>::Ptr',
}

class IDLType(object):
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

    def cppType(self, opt_sp=False):
        """Gets the C++ type declaration of this IDL type.

        The opt_sp puts a trailing space after a closing angle bracket
        if the type itself ends with a closing angle bracket.
        """
        sp = ' ' if opt_sp and self.name in COMPOUND else ''
        if self.elem_type is None:
            return CPP_TYPE[self.name] + sp
        return CPP_TYPE[self.name] % self.elem_type.cppType(opt_sp=True) + sp

    def cppArgType(self):
        """Gets the C++ type declaration for a function parameter.

        The only difference from the usual cppType is that we pass
        compound types and strings by const reference.
        """
        type = self.cppType()
        if self.name in BY_CREF:
            type += ' const&'
        return type

    def __repr__(self):
        if self.elem_type is None:
            return "IDLType('%s')" % self.name
        return "IDLType('%s', %s)" % (self.name, self.elem_type)

class InterfaceDef(object):
    """Represents an interface definition."""
    def __init__(self, cls, method_list):
        self.cls = cls
        self.method_list = method_list
