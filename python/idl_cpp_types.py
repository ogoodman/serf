"""Specialises IDL types for C++ code generation."""

from serf import idl_types

# NOTE: remove imports whenever they are sub-classed.
from serf.idl_types import COMPOUND, InterfaceDef, ExceptionDef

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


class IDLType(idl_types.IDLType):
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

    def writeCppInitArg(self, out, i):
        """Write code to declare and initialize a<i> from args.at(<i>)."""
        cpp_type = self.cppType()
        if self.name == 'var':
            out.writeln('%s a%d(args.at(%d));' % (cpp_type, i, i))
        elif self.name in COMPOUND:
            out.writeln('%s a%d;' % (cpp_type, i))
            out.writeln('extract(a%d, args.at(%d));' % (i, i))
        else:
            out.writeln('%s a%d(boost::get<%s>(args.at(%d)));' % (cpp_type, i, cpp_type, i))
    
class ProxyType(idl_types.ProxyType):
    def cppType(self, opt_sp=False):
        """Returns the C++ type declaration for this proxy type."""
        return self.type_name + 'Prx'

    def cppArgType(self):
        """Returns the preferred C++ parameter type."""
        return self.type_name + 'Prx const&'

    def writeCppInitArg(self, out, i):
        """Write code to declare and initialize a<i> from args.at(<i>)."""
        cpp_type = self.cppType()
        out.writeln('%s a%d(rpc, boost::get<serf::Record const&>(args.at(%d)));' % (cpp_type, i, i))

class Member(idl_types.Member):
    def writeInitMember(self, out):
        """Write code to initialize a struct member."""
        var_value = 'M(value)["%s"]' % self.name
        if self.type.name in COMPOUND:
            out.writeln('extract(%s, %s);' % (self.name, var_value))
        else:
            cref_type = self.type.cppArgType()
            out.writeln('%s = boost::get<%s>(%s);' % (self.name, cref_type, var_value))
