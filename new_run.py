from instance_structure import InstanceStructure
from PySP import GBB, RLT, BigM
from Function_Module import perc, curr, ptime
from collections import defaultdict
from Crispin.bash import id_generator
from Crispin.context import temp_file
import Crispin.bash as bash

import itertools
import string
import random
import math

mean = lambda l: sum(l)/float(len(l))
stdev = (lambda s: math.sqrt(mean(map(lambda x: (x - mean(s))**2, s))))

funcs = {'GBB': GBB, 'RLT':RLT, 'BigM': BigM}

SVP = [3]
IJ = [3,5]
T = [3]
K = [5,10]
case_list = list(itertools.product(SVP, SVP, SVP, IJ, T, K))
case_list = sorted(case_list, key=lambda k: k[3])
case_list = sorted(case_list, key=lambda k: k[5])
cases = [(s, v, p, b, b, c, d) for (s, v, p, b, c, d) in case_list]


# Code to help create non symmetric case lists
'''
tk = lambda (t,k): (3,3,3,t,t,3,k)
case_remove = lambda entry: cases.pop(cases.index(entry))
priority = lambda t,k:[case_remove(tk((t,k)))] + cases

cases = priority(15,50)
cases = priority(15,20)
#cases = priority(10,20)

print cases

done_cases = [(3,5), (5,5), (10,5), (15,5),
              (3,10),(5,10),(10,10),
              (3,20),(5,20),(10,20),
              (3,50),(5,50)]

map(case_remove,map(tk,done_cases))

cases = [(3,3,3,3,3,3,3)]
'''

N = len(cases)
# M1 is the number of times of running different instances of the same size
M1 = 2
# M2 is the number of times running the same instance
M2 = 1

# Code will run N * M1 * M2 times

ID = id_generator()
print 'TEST ID: {}\n'.format(ID)
with open('Results/Results_{}.txt'.format(ID), 'w') as f:
    f.write('TEST ID: {}\n'.format(ID))

for idx,case in enumerate(cases):
    objs = defaultdict(dict)
    times = defaultdict(dict)
    print "[{}] (Case {} of {}):".format(','.join(map(str,case)),idx+1,N)

    for m1 in xrange(M1):
        instance = InstanceStructure(*case)
        instance.create_node_data()
        instance.create_scenario_data()
        for m2 in xrange(M2):
            for mthd, app in (('GBB', 'EF'), ('RLT', 'PH'), ('BigM', 'PH')):
                obj, t = funcs[mthd](app)
                objs[mthd, app][m1, m2] = obj
                times[mthd, app][m1, m2] = t

                print '\tRUN TIME [{0:>4}/{1}]: {2}'.format(mthd, app, ptime(t))
            print

    with open('Results/Results_{}.txt'.format(ID), 'a') as f:
        f.write("[{}] (Case {} of {}):\n".format(','.join(map(str,case)),idx+1,N))
        for (app, mthd), d in times.iteritmes:
            thymes = d.values()
            for t in thymes:
                f.write('\tRUN TIME [{}/{}]: {}\n'.format(mthd, app, t))
            else:
                f.write('\n\tMEAN:  {} seconds\n'.format(mean(thymes)))
                f.write('\tSTDEV: {} seconds\n'.format(stdev(thymes)))
                f.write('\tMIN:   {} seconds\n'.format(min(thymes)))
                f.write('\tMAX:   {} seconds\n\n'.format(max(thymes)))