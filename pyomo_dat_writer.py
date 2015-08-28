import itertools
from copy import deepcopy
from collections import OrderedDict


def flatten(x):
    if isinstance(x, basestring):
        return x
    else:
        result = []
        for item in x:
            if hasattr(item, "__iter__") and not isinstance(item, basestring):
                result.extend(flatten(item))
            else:
                result.append(item)
        return tuple(result)


class PyomoDatWriter(object):
    def __init__(self, name):
        self.params = OrderedDict()
        self.sets = OrderedDict()
        self.comments = []
        self.name = name + '.dat'

    def add_header_comment(self, comment):
        self.comments.extend(comment.rstrip().split('\n'))

    def add_set(self, name, data):
        self.sets[name] = data

    def add_param(self, name, data, sets=None):
        if sets is None:
            self.params[name] = data
        else:
            self.params[name] = OrderedDict()
            indices = sets if sets == list(flatten(sets)) else itertools.product(*sets)
            for index in indices:
                self.params[name][index] = data[index]

    def remove_header_comment(self, comment):
        for line in comment.rstrip().split('\n'):
            try:
                comment.remove(line)
            except ValueError:
                print '{} is not a comment of {}'.format(line, self.name)

    def remove_header_comments(self):
        self.comments = []

    def remove_set(self, name):
        try:
            self.sets.pop(name)
        except KeyError:
            print '{} is not a set of {}'.format(name, self.name)

    def remove_sets(self):
        self.sets = OrderedDict()

    def remove_param(self, name):
        try:
            self.params.pop(name)
        except KeyError:
            print '{} is not a parameter of {}'.format(name, self.name)

    def remove_params(self):
        self.params = OrderedDict()

    def copy(self, name):
        temp = deepcopy(self)
        temp.name = name + '.dat'
        return temp

    def write(self):
        with open(self.name, 'w') as DAT_FILE:
            DAT_FILE.writelines('\n'.join(['# {}'.format(comment) for comment in self.comments]))
            DAT_FILE.write('\n\n')

            for name, data in self.sets.iteritems():
                header_line = 'set {} :='.format(name)
                line = header_line

                for datum in data:
                    if len(line) < 80:
                        line += ' ' + datum
                    else:
                        DAT_FILE.write(line + '\n')
                        line = ' ' * len(header_line)
                else:
                    DAT_FILE.write(line + ';\n\n')

            for name, data in self.params.iteritems():
                if isinstance(data, dict):
                    header_line = 'param {} := '.format(name)
                    for i, (index, datum) in enumerate(data.iteritems()):
                        if i == 0:
                            line = header_line
                        else:
                            line = ' ' * len(header_line)
                        label = index if isinstance(index, basestring) else ' '.join(index)
                        DAT_FILE.write(line + '{} {}\n'.format(label, datum))
                    else:
                        DAT_FILE.write(';\n\n')
                else:
                    DAT_FILE.write('param {} := {}; \n\n'.format(name, data))


if __name__ == '__main__':
    stores = ["s" + str(s + 1) for s in xrange(3)]
    vendors = ["v" + str(v + 1) for v in xrange(3)]
    products = ["p" + str(p + 1) for p in xrange(3)]
    times = ["t" + str(t + 1) for t in xrange(3)]

    gamma = 1

    # Data for holding cost for product p at the warehouse
    Cz = {tup: 0.05 for tup in itertools.chain(products, itertools.product(stores, products))}

    # Data for backlog cost for product p at store s
    Cr = {p: .10 for p in products}

    dat = PyomoDatWriter('test')
    dat.add_set('STORES', stores)
    dat.add_set('PRODUCTS', products)
    dat.add_set('VENDORS', vendors)
    dat.add_set('TIMES', times)

    dat.add_param('FractionalFullTimeLoad', gamma)
    dat.add_param('ProductHoldingCostStore', Cz, [stores, products])
    dat.add_param('ProductHoldingCostWarehouse', Cz, products)

    dat.add_header_comment('The Force be with you\n\tYoung Jedi')

    dat.write()
