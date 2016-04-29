"""A function to merge two records into one."""

class MergeTerm(object):
    serialize = ('source', 'fieldIn', 'fieldOut')

    def __init__(self, source, fieldIn, fieldOut):
        self.source = source
        self.fieldIn = fieldIn
        self.fieldOut = fieldOut

def setField(i_pk, i_rec, f, o_f, o_rec, o_done):
    if o_f not in o_done:
        try:
            o_rec[o_f] = (i_pk if f == '#' else i_rec[f])
        except KeyError:
            pass
        o_done.add(o_f)

def mergeRecords(l_pk, l_rec, r_pk, r_rec, spec, o_rec):
    l_done = set()
    r_done = set()
    o_done = set()
    for term in spec:
        lr, f_in, f_out = term.source, term.fieldIn, term.fieldOut
        if term.source not in 'LR':
            print 'bad spec term MergeTerm%r' % ((lr, f_in, f_out),)
            continue
        i_pk, i_rec, i_done = (
            (l_pk, l_rec, l_done) if lr == 'L' else (r_pk, r_rec, r_done))

        if f_in == '*':
            if '%' not in f_out:
                print 'bad spec term MergeTerm%r' % ((lr, f_in, f_out),)
                continue
            for f in i_rec.keys():
                if f in i_done:
                    continue
                i_done.add(f)
                o_f = f_out.replace('%', f)
                setField(i_pk, i_rec, f, o_f, o_rec, o_done)
        else:
            if f_in in i_done:
                continue
            i_done.add(f_in)
            if f_out == '.':
                continue
            setField(i_pk, i_rec, f_in, f_out, o_rec, o_done)
    return o_rec

def makeTerm(text):
    """Converts a merge term string to a MergeTerm

    A merge term takes the form 
        <source>:<field-in>[-><field-out>]
    where <source> is 'L' or 'R', <field-in> specifies which
    field(s) to read from the source record, and <field-out> specifies
    which field(s) to write to the output record.

    NOTE: L is the stream, R is the table.
 
    The source field, <field-in> may be
        the name of a field,
        '*' meaning all fields, or
        '#' meaning the primary key of the source record.
    The output field may be
        the name of a field,
        when the source is *, a template containing a % which is substituted,
        '.' meaning the value is to be discarded.
    If no output field is specified, the output field defaults to
        the input field name when it is not special, or
        '%' when the input field is '*'.
    """
    source, field_in = text.split(':', 1)
    if source not in 'LR':
        raise Exception('Bad merge term:%r' % text)
    field_bits = field_in.split('->', 1)
    if len(field_bits) == 2:
        field_in, field_out = field_bits
    else:
        if field_in == '*':
            field_out = '%'
        elif field_in == '#':
            raise Exception('Bad merge term:%r' % text)
        else:
            field_out = field_in
    return MergeTerm(source, field_in, field_out)

def mergeSpec(text):
    return map(makeTerm, text.split())
    
