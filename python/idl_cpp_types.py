"""Specialises IDL types for C++ code generation."""

from cStringIO import StringIO
from serf import idl_types

# NOTE: remove imports whenever they are sub-classed.
from serf.idl_types import COMPOUND

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
    
    def reprExpr(self, name):
        """Write expression for a representation of a value of this type."""
        if self.name == 'void':
            return '"void"';
        if self.name == 'future':
            return '"future<%s>"' % self.elem_type.name
        if self.name in ('bool', 'byte', 'ascii', 'text', 'data'):
            return 'repr(%s)' % name
        return name


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

class InterfaceDef(idl_types.InterfaceDef):
    def writeMethodDispatch(self, out, method, arg_types, return_type):
        """Generate method calling code for a servant base."""
        # Check it all makes sense.
        min_len = len(arg_types)
        for i, a_type in enumerate(arg_types):
            assert(a_type.name != 'void')
            if a_type.opt:
                min_len = i
            if i > min_len:
                assert(a_type.opt) # All must be optional after the first such.
        assert(min_len == len(arg_types)) # TODO: do opt args code after.

        out.writeln('if (method == "%s") {' % method)
        out.indent(1)
        if min_len > 0:
            out.writeln('if (args.size() < %d) throw serf::NotEnoughArgs(method, args.size(), %d);' % (min_len, min_len))

        # Initialize the arguments we will present.
        for i, a_type in enumerate(arg_types):
            a_type.writeCppInitArg(out, i)

        # Generate the call.
        params = ['a%d' % i for i in xrange(len(arg_types))]
        call = '%s(%s)' % (method, ', '.join(params))
        if return_type.name == 'void':
            out.writeln('%s;' % call)
        elif return_type.name == 'future':
            future_type = return_type.elem_type
            out.writeln('return toFuture<%s >(%s);' % (future_type.cppType(), call))
        elif return_type.name in COMPOUND:
            out.writeln('%s r(%s);' % (return_type.cppType(), call))
            out.writeln('setVar(result, r);')
        else:
            out.writeln('result = %s;' % call)
        out.indent(-1)
        out.write('}')

    def writeServantBaseImpl(self, out):
        """Generate code for the varCall_a_ method of a servant base."""
        out.writeln('serf::FVarP %s::varCall_a_(std::string const& method, std::vector<serf::Var> const& args, serf::VarCaller* rpc) {' % self.cls)
        out.indent(1)
        out.writeln('serf::Var result;')
        first = True
        for spec in self.method_list:
            if not first:
                out.write(' else ')
            first = False
            self.writeMethodDispatch(out, *spec)
        if self.method_list:
            out.writeln(' else {')
        out.indent(1)
        out.writeln('throw serf::NoSuchMethod(method);')
        out.indent(-1)
        if self.method_list:
            out.writeln('}')
        out.writeln('return encodeResult_(result);');
        out.indent(-1)
        out.writeln('}')

    def writeProxyMethodImpl(self, out, method, arg_types, return_type):
        """Generate a method declaration for a proxy class."""
        args = ', '.join(['%s a%d' % (a_type.cppArgType(), i) for i, a_type in enumerate(arg_types)])
        if return_type.name != 'future':
            return_type = IDLType('future', return_type)
        base_return_type = return_type.elem_type
        out.writeln('%s %sPrx::%s(%s) {' % (return_type.cppType(), self.cls, method, args))
        out.indent(1)
        out.writeln('std::vector<serf::Var> args(%d);' % len(arg_types))
        # Proxy arguments
        for i, a_type in enumerate(arg_types):
            if a_type.name in COMPOUND:
                out.writeln('setVar(args[%d], a%d);' % (i, i))
            else:
                out.writeln('args[%d] = a%d;' % (i, i))
        # Proxy return value
        out.writeln('return toFuture<%s >(call_("%s", args));' % (base_return_type.cppType(), method))
        out.indent(-1)
        out.writeln('}')
    
    def writeProxyClassImpl(self, out):
        """Generate implementation of a Proxy class."""    
        out.writeln('%sPrx::%sPrx(serf::VarCaller* remote, std::string const& node, std::string const& addr) : serf::VarProxy(remote, node, addr) {\n}' % (self.cls, self.cls))
        out.writeln('%sPrx::%sPrx(serf::VarCaller* remote, serf::Record const& rec) : serf::VarProxy(remote, rec) {\n}' % (self.cls, self.cls))
        out.writeln('%sPrx::%sPrx() : serf::VarProxy(NULL, "", "") {}' % (self.cls, self.cls))
        for spec in self.method_list:
            self.writeProxyMethodImpl(out, *spec)

    def writeServantMethodDecl(self, out, method, arg_types, return_type):
        """Writes a method declaration for a servant base class."""
        args = ', '.join([a_type.cppArgType() for a_type in arg_types])
        rtype = return_type.cppType()
        out.writeln('virtual %s %s(%s) = 0;' % (rtype, method, args))

    def writeServantBaseDecl(self, out):
        """Generate code for the servant base class declaration."""
        out.writeln('class %sPrx;' % self.cls)
        out.writeln('')
        out.writeln('class %s : public serf::VarCallable {' % self.cls)
        out.writeln('public:')
        out.indent(1)
        for spec in self.method_list:
            self.writeServantMethodDecl(out, *spec)
        out.writeln('virtual serf::FVarP varCall_a_(std::string const& method, std::vector<serf::Var> const& args, serf::VarCaller* rpc);')
        out.indent(-1)
        out.writeln('};')

    def writeProxyMethodDecl(self, out, method, arg_types, return_type):
        """Generate a method declaration for a proxy class."""
        assert('future' not in [a_type.name for a_type in arg_types])
        args = ', '.join([a_type.cppArgType() for a_type in arg_types])
        if return_type.name != 'future':
            return_type = IDLType('future', return_type)
        out.writeln('%s %s(%s);' % (return_type.cppType(), method, args))

    def writeProxyClassDecl(self, out):
        """Generate a proxy class declaration."""
        out.writeln('class %sPrx : public serf::VarProxy {' % self.cls)
        out.writeln('public:')
        out.indent(1)
        out.writeln('%sPrx(serf::VarCaller* remote, std::string const& node, std::string const& addr);' % self.cls)
        out.writeln('%sPrx(serf::VarCaller* remote, serf::Record const& rec);' % self.cls)
        out.writeln('%sPrx();' % self.cls)
        out.writeln('')
        for spec in self.method_list:
            self.writeProxyMethodDecl(out, *spec)
        out.indent(-1)
        out.writeln('};')

    def writeDecl(self, out):
        """Write servant base and proxy class declarations."""
        self.writeServantBaseDecl(out)
        out.writeln('')
        self.writeProxyClassDecl(out)

    def writeDef(self, out):
        """Write servant base and proxy class implemenations."""
        self.writeServantBaseImpl(out)
        out.writeln('')
        self.writeProxyClassImpl(out)

class Member(idl_types.Member):
    def writeDecl(self, out):
        """Write the member declaration as used in a class body."""
        out.writeln('%s %s;' % (self.type.cppType(), self.name))

    def argDecl(self, underscored=False):
        """Write declaration as used in a constructor argument list."""
        suffix = '_' if underscored else ''
        return '%s %s%s' % (self.type.cppArgType(), self.name, suffix)

    def writeInitMember(self, out, i=None):
        """Write code to initialize a struct member."""
        if i is not None:
            var_value = 'args.at(%d)' % i
        else:
            var_value = 'M(value)["%s"]' % self.name
        if self.type.name in COMPOUND:
            out.writeln('extract(%s, %s);' % (self.name, var_value))
        else:
            cref_type = self.type.cppArgType()
            out.writeln('%s = boost::get<%s>(%s);' % (self.name, cref_type, var_value))

    def writeInitListItem(self, out, i=None):
        """Code to initialize a member in the constructor init list."""
        if i is not None:
            var_value = 'args.at(%d)' % i
        else:
            var_value = 'M(value)["%s"]' % self.name
        if self.type.name not in COMPOUND:
            cref_type = self.type.cppArgType()
            out.write('%s(boost::get<%s>(%s))' % (self.name, cref_type, var_value))

class ExceptionDef(idl_types.ExceptionDef):
    def argList(self, underscored=False):
        """Writes the argument list for a simple memberwise constructor."""
        return ', '.join([m.argDecl(underscored) for m in self.member_list])
    
    def writeDecl(self, out):
        """Writes a user-defined exception class."""
        out.writeln('class %s : public serf::SerfException' % self.cls)
        out.writeln('{')
        # Constructors.
        out.writeln('public:')
        out.indent(1)
        out.writeln('%s(%s);' % (self.cls, self.argList()))
        out.writeln('%s(std::vector<serf::Var> const& args);' % self.cls);
        out.writeln('~%s() throw() {}' % self.cls);
        out.writeln('')
        out.writeln('serf::Var encode() const;')
        out.writeln('std::string type() const;')
        out.writeln('const char* what() const throw();')
        out.indent(-1)
        # Members.
        out.writeln('public:')
        out.indent(1)
        for m in self.member_list:
            m.writeDecl(out)
        out.indent(-1)
        out.writeln('};')

    def writeConstructorDef(self, out):
        """Writes code for memberwise constructor."""
        out.writeln('%s::%s(%s) :' % (self.cls, self.cls, self.argList(underscored=True)))
        out.indent(1)
        first = True
        for m in self.member_list:
            if not first:
                out.writeln(',')
            first = False
            out.write('%s(%s_)' % (m.name, m.name))
        out.writeln(' {}')
        out.indent(-1)

    def writeVarConstructorDef(self, out):
        """Writes code to construct an exception from a vector<Var>."""
        out.writeln('%s::%s(std::vector<serf::Var> const& args) :' % (self.cls, self.cls))
        out.indent(1)
        body_m = []
        first = True
        for i, m in enumerate(self.member_list):
            if m.type.name in COMPOUND:
                body_m.append((i, m))
            else:
                if not first:
                    out.writeln(',')
                m.writeInitListItem(out, i + 1)
                first = False
        out.writeln(' {')
        for i, m in body_m:
            m.writeInitMember(out, i + 1)
        out.indent(-1)
        out.writeln('}')

    def writeEncodeDef(self, out):
        """Writes code to encode an exception as a Var."""
        out.writeln('serf::Var %s::encode() const {' % self.cls)
        out.indent(1)
        out.writeln('std::vector<serf::Var> enc(%d);' % (len(self.member_list) + 1))
        out.writeln('enc[0] = std::string("%s");' % self.cls)
        for i, m in enumerate(self.member_list):
            if m.type.name in COMPOUND:
                out.writeln('setVar(enc[%d], %s);' % (i + 1, m.name))
            else:
                out.writeln('enc[%d] = %s;' % (i + 1, m.name))
        out.writeln('return enc;')
        out.indent(-1)
        out.writeln('}')

    def writeTypeDef(self, out):
        """Writes code for the type() method."""
        out.writeln('std::string %s::type() const {' % self.cls)
        out.indent(1)
        out.writeln('return "%s";' % self.cls)
        out.indent(-1)
        out.writeln('}')

    def writeWhatDef(self, out):
        """Writes code for the what() method."""
        out.writeln('const char* %s::what() const throw() {' % self.cls)
        out.indent(1)
        out.writeln('std::ostringstream out;')
        out.writeln('out << "%s(";' % self.cls)
        csep = ''
        for m in self.member_list:
            out.writeln('out %s<< "%s=" << %s;' % (csep, m.name, m.type.reprExpr(m.name)))
            csep = '<< ", " '
        out.writeln('out << ")";')
        out.writeln('msg_ = out.str();')
        out.writeln('return msg_.c_str();')
        out.indent(-1)
        out.writeln('}')

    def writeDef(self, out):
        """Write code defining all class members."""
        self.writeConstructorDef(out)
        out.writeln('')
        self.writeVarConstructorDef(out)
        out.writeln('')
        self.writeEncodeDef(out)
        out.writeln('')
        self.writeTypeDef(out)
        out.writeln('')
        self.writeWhatDef(out)

    def writeRegistration(self, out):
        out.writeln('serf::Exceptions::add("%s", new serf::Thrower<%s>);' % (self.cls, self.cls))

def writeExceptionRegistration(out, exc):
    if not exc:
        return
    out.writeln('static void registerExc() {')
    out.indent(1)
    for e in exc:
        e.writeRegistration(out)
    out.indent(-1)
    out.writeln('}')
    out.writeln('static serf::OnLoad run(registerExc);')
