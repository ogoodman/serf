#!/usr/bin/python
"""Convert the contents of an IDL file to C++.

Usage:
    idl_to_cpp <name>.serf <output-dir>

Writes <output-dir>/<name>_gen.cpp and <output-dir>/<name>_gen.h
containing generated code for servant base classes and proxies
for each interface defined in <name>.serf.
"""

import os, sys
from pprint import pprint
from pyparsing import ParseException
from serf.idl_types import COMPOUND, IDLType, InterfaceDef
from serf.idl_parser import idl_parser, addParseActions
from serf.util import getOptions

addParseActions()

class IndentingStream(object):
    """Wrapper for a file-like object which handles indentation."""
    def __init__(self, out):
        self.level = 0
        self.out = out
        self.done_indent = False

    def writeln(self, line):
        """Write line to self.out indented by the current level."""
        if not self.done_indent:
            self.out.write('    ' * self.level)
        self.out.write(line)
        self.out.write('\n')
        self.done_indent = False

    def write(self, s):
        """Write s to self.out indenting each line by the current level."""
        lines = s.split('\n')
        for line in lines[:-1]:
            self.writeln(line)
        if lines[-1]:
            if not self.done_indent:
                self.out.write('    ' * self.level)
            self.out.write(lines[-1])
            self.done_indent = True

    def indent(self, n):
        """Add n to the current indent level."""
        self.level += n

def writeMethodDispatch(out, method, arg_types, return_type):
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

def writeServantBaseImpl(out, cls, method_list):
    """Generate code for the varCall_a_ method of a servant base."""
    out.writeln('serf::FVarP %s::varCall_a_(std::string const& method, std::vector<serf::Var> const& args) {' % cls)
    out.indent(1)
    out.writeln('serf::Var result;')
    first = True
    for spec in method_list:
        if not first:
            out.write(' else ')
        first = False
        writeMethodDispatch(out, *spec)
    if method_list:
        out.writeln(' else {')
    out.indent(1)
    out.writeln('throw serf::NoSuchMethod(method);')
    out.indent(-1)
    if method_list:
        out.writeln('}')
    out.writeln('return encodeResult_(result);');
    out.indent(-1)
    out.writeln('}')

def writeServantMethodDecl(out, method, arg_types, return_type):
    """Writes a method declaration for a servant base class."""
    args = ', '.join([a_type.cppArgType() for a_type in arg_types])
    rtype = return_type.cppType()
    out.writeln('virtual %s %s(%s) = 0;' % (rtype, method, args))

def writeServantBaseDecl(out, cls, method_list):
    """Generate code for the servant base class declaration."""
    out.writeln('class %s : public serf::VarCallable {' % cls)
    out.writeln('public:')
    out.indent(1)
    for spec in method_list:
        writeServantMethodDecl(out, *spec)
    out.writeln('virtual serf::FVarP varCall_a_(std::string const& method, std::vector<serf::Var> const& args);')
    out.indent(-1)
    out.writeln('};')

def writeProxyMethodDecl(out, method, arg_types, return_type):
    """Generate a method declaration for a proxy class."""
    assert('future' not in [a_type.name for a_type in arg_types])
    args = ', '.join([a_type.cppArgType() for a_type in arg_types])
    if return_type.name != 'future':
        return_type = IDLType('future', return_type)
    out.writeln('%s %s(%s);' % (return_type.cppType(), method, args))

def writeProxyClassDecl(out, cls, method_list):
    """Generate a proxy class declaration."""
    out.writeln('class %sPrx : public serf::VarProxy {' % cls)
    out.writeln('public:')
    out.indent(1)
    out.writeln('%sPrx(serf::VarCaller* remote, std::string const& node, std::string const& addr);' % cls)
    out.writeln('%sPrx(serf::VarCaller* remote, serf::Record const& rec);' % cls)
    out.writeln('')
    for spec in method_list:
        writeProxyMethodDecl(out, *spec)
    out.indent(-1)
    out.writeln('};')

def writeProxyMethodImpl(out, cls, method, arg_types, return_type):
    """Generate a method declaration for a proxy class."""
    args = ', '.join(['%s a%d' % (a_type.cppArgType(), i) for i, a_type in enumerate(arg_types)])
    if return_type.name != 'future':
        return_type = IDLType('future', return_type)
    base_return_type = return_type.elem_type
    out.writeln('%s %sPrx::%s(%s) {' % (return_type.cppType(), cls, method, args))
    out.indent(1)
    out.writeln('std::vector<serf::Var> args(%d);' % len(arg_types))
    for i, a_type in enumerate(arg_types):
        if a_type.name in COMPOUND:
            out.writeln('setVar(args[%d], a%d);' % (i, i))
        else:
            out.writeln('args[%d] = a%d;' % (i, i))
    out.writeln('return toFuture<%s >(call_("%s", args));' % (base_return_type.cppType(), method))
    out.indent(-1)
    out.writeln('}')
    
def writeProxyClassImpl(out, cls, method_list):
    """Generate implementation of a Proxy class."""    
    out.writeln('%sPrx::%sPrx(serf::VarCaller* remote, std::string const& node, std::string const& addr) : serf::VarProxy(remote, node, addr) {\n}' % (cls, cls))
    out.writeln('%sPrx::%sPrx(serf::VarCaller* remote, serf::Record const& rec) : serf::VarProxy(remote, rec) {\n}' % (cls, cls))
    for spec in method_list:
        writeProxyMethodImpl(out, cls, *spec)

def writeCppHeader(out, interfaces, name):
    """Write header file containing servant base and proxy declarations."""
    guard_id = 'IDL_GENERATED_%s_HGUARD_' % name.upper()
    out.writeln('#ifndef %s' % guard_id)
    out.writeln('#define %s' % guard_id)
    out.writeln('')
    out.writeln('// GENERATED CODE -- DO NOT EDIT!')
    out.writeln('')
    out.writeln('#include <serf/rpc/var_callable.h>')
    out.writeln('#include <serf/rpc/var_proxy.h>')
    out.writeln('')
    for i in interfaces:
        writeServantBaseDecl(out, i.cls, i.method_list)
        out.writeln('')
        writeProxyClassDecl(out, i.cls, i.method_list)
        out.writeln('')
    out.writeln('#endif // %s' % guard_id)

def writeCppSource(out, interfaces, name):
    """Write source file implementing servant base and proxy."""
    out.writeln('#include "%s.h"' % name)
    out.writeln('')
    out.writeln('// GENERATED_CODE -- DO NOT EDIT!')
    out.writeln('')
    out.writeln('#include <serf/serializer/extract.h>')
    out.writeln('#include <serf/rpc/var_caller.h>')
    out.writeln('#include <serf/rpc/serf_exception.h>')
    out.writeln('')
    for i in interfaces:
        writeServantBaseImpl(out, i.cls, i.method_list)
        out.writeln('')
        writeProxyClassImpl(out, i.cls, i.method_list)
        out.writeln('')

def writeFiles(outdir, name, interfaces):
    path = os.path.join(outdir, name + '.h')
    with open(path, 'w') as f_out:
        out = IndentingStream(f_out)
        writeCppHeader(out, interfaces, name)
    print 'wrote', path
    path = os.path.join(outdir, name + '.cpp')
    with open(os.path.join(outdir, name + '.cpp'), 'w') as f_out:
        out = IndentingStream(f_out)
        writeCppSource(out, interfaces, name)
    print 'wrote', path

def main():
    opt, args = getOptions('h', ['help'], __doc__)
    src_file = args[0]
    src = open(src_file).read()
    try:
        tokens = idl_parser.parseString(src, parseAll=True)
    except ParseException as err:
        print err.line
        print ' ' * (err.column-1) + '^'
        print err
        return
    name = src_file.rsplit('.', 1)[0] + '_gen'
    interfaces = [t for t in tokens if type(t) is InterfaceDef]
    if len(args) > 1:
        writeFiles(args[1], name, interfaces)
    else:
        out = IndentingStream(sys.stdout)
        writeCppHeader(out, interfaces, name)
        writeCppSource(out, interfaces, name)


if __name__ == '__main__':
    main()

