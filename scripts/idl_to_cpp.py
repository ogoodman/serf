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
from serf import idl_cpp_types
from serf.idl_cpp_types import COMPOUND, IDLType, InterfaceDef
from serf.idl_parser import idl_parser, addParseActions
from serf.util import getOptions, IndentingStream

addParseActions(idl_cpp_types)

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
    out.writeln('#include <serf/rpc/serf_exception.h>')
    out.writeln('')
    for i in interfaces:
        i.writeDecl(out)
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
    out.writeln('#include <serf/util/debug.h>')
    out.writeln('')
    for i in interfaces:
        i.writeDef(out)
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
        items = idl_parser.parseString(src, parseAll=True)
    except ParseException as err:
        print err.line
        print ' ' * (err.column-1) + '^'
        print err
        return
    name = src_file.rsplit('.', 1)[0] + '_gen'
    if len(args) > 1:
        writeFiles(args[1], name, items)
    else:
        out = IndentingStream(sys.stdout)
        writeCppHeader(out, items, name)
        writeCppSource(out, items, name)


if __name__ == '__main__':
    main()

