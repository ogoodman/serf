"""What capabilities should really look like."""

from fred.obj import obj

def Printer():
    def pr(*x):
        for item in x:
            print item,
        if x:
            print
    return obj(printer=obj(pr=pr))

def Queue(printer=None, name='<queue>'):
    data = []

    def get():
        return data.pop(0)

    def put(item):
        data.append(item)

    def pr():
        printer.pr(data)

    def lput(item):
        printer.pr('put:', item, '->', name)
        put(item)

    def lget():
        item = get()
        printer.pr('get:', item, '<-', name)
        return item

    def size():
        return len(data)

    return obj(
        getter=obj(get=get),
        putter=obj(put=put),
        lputter=obj(put=lput),
        lgetter=obj(get=lget),
        inspecter=obj(pr=pr, size=size))

def demo(putter, getter, inspecter, p):
    putter.put(1)
    inspecter.pr()
    p.pr(getter.get())

if __name__ == '__main__':
    p = Printer().printer
    q = Queue(printer=p)

    demo(q.putter, q.getter, q.inspecter, p)
    demo(q.lputter, q.lgetter, q.inspecter, p)



