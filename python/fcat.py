#!/usr/bin/python

"""Print contents of a storage slot.

Synopsis:
    fcat <filename>
"""

import os
from fred.serialize import decodes, Record
from fred.util import getOptions

def main():
    opt, args = getOptions('-hn')
    filename = args[0]
    data = open(filename).read()
    value = decodes(data, Record)
    dir, name = os.path.split(filename)
    is_name = dir.endswith('names') or opt('-n')
    if is_name and type(value) is Record and value.name == 'ref':
        try:
            data = open(os.path.join(dir, '../caps', value.data['path'])).read()
        except IOError:
            pass
        else:
            value = decodes(data)
    print value

if __name__ == '__main__':
    main()
