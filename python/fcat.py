#!/usr/bin/python

"""Print contents of a storage slot.

Synopsis:
    fcat <filename>
"""

import os, sys
from serf.serializer import decodes, Record
from serf.util import getOptions
try:
    from serf import config
except ImportError:
    pass

def pw(f, data, lev=0):
    t = type(data)
    if t is dict:
        f.write('{\n')
        for k, v in data.items():
            f.write('  ' * (lev+1))
            f.write(repr(k))
            f.write(': ')
            pw(f, v, lev+1)
            f.write(',\n')
        f.write('  ' * lev)
        f.write('}')
    elif t is list:
        f.write('[\n')
        for v in data:
            f.write('  ' * (lev+1))
            pw(f, v, lev+1)
            f.write(',\n')
        f.write('  ' * lev)
        f.write(']')
    elif t is Record:
        if data.type_name == 'inst' and 'CLS' in data.value:
            d = dict(data.value)
            cls = d.pop('CLS')
            f.write('%s(\n' % cls)
            for k, v in d.iteritems():
                f.write('  ' * (lev+1))
                f.write('%s = ' % k)
                pw(f, v, lev+1)
                f.write(',\n')
            f.write('  ' * lev)
            f.write(')')
        else:
            f.write('%s(' % data.type_name)
            pw(f, data.value, lev+1)
            f.write(')')
    else:
        f.write(repr(data))

def main():
    opt, args = getOptions('-hn')
    filename = args[0]
    data = open(filename).read()
    value = decodes(data)
    dir, name = os.path.split(filename)
    is_name = dir.endswith('names') or opt('-n')
    if is_name and type(value) is Record and value.name == 'ref':
        try:
            data = open(os.path.join(dir, '../caps', value.data['path'])).read()
        except IOError:
            pass
        else:
            value = decodes(data, check=False)
    pw(sys.stdout, value)
    print

if __name__ == '__main__':
    main()
