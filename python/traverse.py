"""Function to apply a given function recursively to a JSON structure.

fn should either return a replacement value for its argument or return None.
Each part of the structure on which fn returns a non-None value is replaced.
"""

def traverseInPlace(data, fn):
    # In-place version
    r = traverse0(data, fn)
    if r is not None:
        return r
    return data

def traverse0(data, fn):
    r = fn(data)
    if r is not None:
        return r
    t = type(data)
    if t is dict:
        for k, v in data.items():
            r = traverse0(v, fn)
            if r is not None:
                data[k] = r
    elif t is list:
        for i, v in enumerate(data):
            r = traverse0(v, fn)
            if r is not None:
                data[i] = r
    return None

def traverse(data, fn):
    r = fn(data)
    if r is not None:
        return r
    t = type(data)
    if t is dict:
        new = {}
        for k, v in data.iteritems():
            new[k] = traverse(v, fn)
    elif t is list:
        new = [traverse(v, fn) for v in data]
    else:
        new = data
    return new
