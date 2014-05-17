"""Function to apply a given function recursively to a JSON structure.

fn should either return a replacement value for its argument or return None.
Each part of the structure on which fn returns a non-None value is replaced.
"""

def traverse(data, fn):
    r = fn(data)
    if r is not None:
        return r
    t = type(data)
    if t is dict:
        new = {}
        for k, v in data.iteritems():
            new[k] = traverse(v, fn)
    elif t in (list, tuple):
        new = [traverse(v, fn) for v in data]
    else:
        new = data
    return new
