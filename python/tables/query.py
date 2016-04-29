import re
from datetime import datetime, timedelta
from serf.serializer import decodes, encodes

MEMSPECI_RE = re.compile('([#@:])([^#@:]+)')
MEMSPEC_RE = re.compile('([#@:][^#@:]+)*$')

GET_FN = {
    '#': (lambda val, index: val[int(index)]),
    ':': (lambda val, key: val[key]),
    '@': getattr
}

def setIndex(val, index, value):
    val[int(index)] = value
def setItem(val, key, value):
    val[key] = value

SET_FN = {
    '#': setIndex,
    ':': setItem,
    '@': setattr
}

def getMember(val, memspec):
    for m in MEMSPECI_RE.finditer(memspec):
        m_type, key = m.groups()
        try:
            val = GET_FN[m_type](val, key)
        except:
            val = None
            break
    return val

def setMember(val, memspec, value):
    path = [m.groups() for m in MEMSPECI_RE.finditer(memspec)]
    for m_type, key in path[:-1]:
        try:
            val = GET_FN[m_type](val, key)
        except:
            val = None
            break
    if val is None:
        return False
    m_type, key = path[-1]
    try:
        SET_FN[m_type](val, key, value)
        return True
    except:
        return False

def checkField(memspec):
    if not MEMSPEC_RE.match(memspec):
        raise ValueError('Invalid field spec %s' % memspec)

class QTerm(object):
    serialize = ('field', 'condition', 'value')

    def __init__(self, field, condition, value=None):
        checkField(field)

        self.field = field
        self.condition = condition
        self.value = value

        self.str_type = value in (str, unicode)

        if condition in ('isnull', 'notnull'):
            if value is not None:
                raise ValueError('Invalid query term %s' % self)

        if condition in ('like', 'unlike'):
            if type(value) not in (str, unicode):
                raise ValueError('Invalid query term %s' % self)
            self.value = value.lower()

        self.test_fn = getattr(self, 'check_' + condition)

    def type_mismatch(self):
        return self.condition in ('ne', 'unlike')

    def check_isnull(self, rec_value, value):
        return rec_value is None
    def check_notnull(self, rec_value, value):
        return rec_value is not None
    def check_eq(self, rec_value, value):
        return rec_value == value
    def check_ne(self, rec_value, value):
        return rec_value != value
    def check_le(self, rec_value, value):
        return rec_value <= value
    def check_ge(self, rec_value, value):
        return rec_value >= value
    def check_like(self, rec_value, value):
        return value in rec_value.lower()
    def check_unlike(self, rec_value, value):
        return value not in rec_value.lower()

    def match(self, rec):
        value = self.value
        rec_value = getMember(rec, self.field)

        if self.condition not in ('isnull', 'notnull'):
            t_val = type(value)
            t_rec_val = type(rec_value)

            if t_val in (str, unicode):
                if t_rec_val not in (str, unicode):
                    return self.type_mismatch()
                # Only compare as unicode if both value are.
                if t_val is unicode and t_rec_val is str:
                    value = value.encode('utf8')
                elif t_val is str and t_rec_val is unicode:
                    rec_val = rec_val.encode('utf8')
            elif t_val in (int, long, float):
                if t_rec_val not in (int, long, float):
                    return self.type_mismatch()
            elif t_val is not t_rec_val:
                return self.type_mismatch()

        return self.test_fn(rec_value, value)

class QAnd(object):
    serialize = ('seq',)

    def __init__(self, seq):
        self.seq = seq

    def match(self, rec):
        for query in self.seq:
            if not query.match(rec):
                return False
        return True

class QOr(object):
    serialize = ('seq',)

    def __init__(self, seq):
        self.seq = seq

    def match(self, rec):
        for query in self.seq:
            if query.match(rec):
                return True
        return False

class QNot(object):
    serialize = ('query',)

    def __init__(self, query):
        self.query = query

    def match(self, rec):
        return not self.query.match(rec)

class QAlways(object):
    serialize = ('value',)

    def __init__(self, value):
        self.value = value

    def match(self, rec):
        return self.value

class QText(object):
    serialize = ('text',)

    def __init__(self, text):
        self.text = text.lower()

    def match(self, rec):
        return self.text in encodes(rec).lower()

def matchQuery(query, rec):
    if type(rec) is str:
        try:
            rec = decodes(rec)
        except:
            return False
    try:
        return query.match(rec)
    except KeyError:
        raise Exception('Unexpected query type %s' % query.__class__)

class QDate(object):
    serialize = ('field', 'year', 'month', 'day')

    def __init__(self, field, year=0, month=0, day=0):
        checkField(field)
        self.field = field
        self.year = year
        self.month = month
        self.day = day

    def match(self, rec):
        dt = getMember(rec, self.field)
        if type(dt) is not datetime:
            print 'not a datetime', dt
            return False
        q_day = self.day
        if q_day < 0:
            dt = dt + timedelta(days=-q_day)
            q_day = 1
        return (q_day in (0, dt.day) and
                self.month in (0, dt.month) and
                self.year in (0, dt.year))

