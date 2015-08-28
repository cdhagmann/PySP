import itertools
from itertools import chain, product


def flatten(x):
    result = []
    for item in x:
        if hasattr(item, "__iter__") and not isinstance(item, basestring):
            result.extend(flatten(item))
        else:
            result.append(item)
    return tuple(result)


def tup_list(*args):
    if len(args) == 1:
        return tuple(*args)
    else:
        return tuple(itertools.imap(flatten, product(*args)))


def param_dat(f, name, data, sets=None):
    if sets is None:
        f.write('param {} := {}; \n\n'.format(name, data))
    else:
        f.write('param {} :=\n'.format(name))
        if sets == list(flatten(sets)):
            tups = tup_list(sets)
            for tup in tups:
                f.write('{} {}\n'.format(tup, data[tup]))
        else:
            tups = tup_list(*sets)
            for tup in tups:
                f.write('{} {}\n'.format(' '.join(tup), data[tup]))
        f.write(';\n\n')


def set_dat(f, name, data):
    f.write('set {} := {};\n\n'.format(name, ' '.join(map(str, data))))


if __name__ == '__main__':
    stores = ["s" + str(s + 1) for s in xrange(3)]
    vendors = ["v" + str(v + 1) for v in xrange(3)]
    products = ["p" + str(p + 1) for p in xrange(3)]
    times = ["t" + str(t + 1) for t in xrange(3)]

    gamma = 1

    # Data for holding cost for product p at the warehouse
    Cz = {tup: 0.05 for tup in chain(products, itertools.product(stores, products))}

    # Data for backlog cost for product p at store s
    Cr = {p: .10 for p in products}

    file_name = 'test.dat'
    f = open(file_name, 'w')

    set_dat(f, 'STORES', stores)
    set_dat(f, 'PRODUCTS', products)
    set_dat(f, 'VENDORS', vendors)
    set_dat(f, 'TIMES', times)

    param_dat(f, 'FractionalFullTimeLoad', gamma)
    param_dat(f, 'ProductHoldingCostWarhouse', Cz, products)
    param_dat(f, 'ProductHoldingCostStore', Cz, [stores, products])

    f.close()
