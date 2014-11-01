import timeit
from bash import pyomo_runef as runef
import Instance
import itertools
import string
import random
import math


''' Generates human readible CPU Times'''
''' Generates human readible CPU Times'''



def htime(s):
    H, s = divmod(s, 3600)
    M, S = divmod(s, 60)
        
    return (H,M,S)

def ptime(s):
    H, M, S = htime(s)
    if float(S) == float(s):
        return '{0:.2f} seconds'.format(s)
    else:
        h = '' if H == 0 else '{}h '.format(H)
        m = '' if M == 0 else '{}m '.format(M)
        t = '({0:.2f} seconds)'.format(s)
        s = '' if S == 0 else '{0:.2f}s '.format(S)
        return h + m + s + t  

mean = lambda l: sum(l)/float(len(l))
stdev = (lambda s: math.sqrt(mean(map(lambda x: (x - mean(s))**2, s))))


L1 = [3]
L2 = [3,5,10,15]
L3 = [3]
L4 = [5,10,20,50]
case_list = list(itertools.product(L1,L1,L1,L2,L3,L4))
case_list = sorted(case_list, key=lambda k: k[3])
case_list = sorted(case_list, key=lambda k: k[5])
cases = [(s,v,p,b,b,c,d) for (s,v,p,b,c,d) in case_list]


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
M1 = 5
# M2 is the number of times running the same instance
M2 = 1

# Code will run N * M1 * M2 times


setup = '''
gc.enable()
from bash import pyomo_runef as runef
from bash import pyomo_runph as runph
'''
def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for x in range(size))

ID = id_generator()
print 'TEST ID: {}\n'.format(ID)
with open('Results/Results_{}.txt'.format(ID), 'w') as f:
    f.write('TEST ID: {}\n'.format(ID))

for idx,case in enumerate(cases):
    data_ef, data_ph = {},{}
    
    print "[{}] (Case {} of {}):".format(','.join(map(str,case)),idx+1,N)
    
    for m1 in xrange(M1):
        Instance.instance_generator(*case)
        for m2 in xrange(M2):
            data_ph[m1,m2] = timeit.Timer('runph()', setup=setup).timeit(1)
            print 'RUN TIME [PH]: {}\n'.format(ptime(data_ph[m1,m2]))
            data_ef[m1,m2] = timeit.Timer('runef()', setup=setup).timeit(1)
            print 'RUN TIME [EF]: {}\n'.format(ptime(data_ef[m1,m2]))
    
    EF = [data_ef[m1,m2] for m1 in xrange(M1) for m2 in xrange(M2)]
    PH = [data_ph[m1,m2] for m1 in xrange(M1) for m2 in xrange(M2)]

    print 'PH RESULTS: {}\n'.format(ptime(mean(PH)))
    print 'EF RESULTS: {}\n'.format(ptime(mean(EF)))
    
    with open('Results/Results_{}.txt'.format(ID), 'a') as f:
        f.write("[{}] (Case {} of {}):\n".format(','.join(map(str,case)),idx+1,N))
        f.write('\nPH RESULTS:\n')
        for data in PH:
            f.write('\tRUN TIME [PH]: {} seconds\n'.format(data))
        else:
            f.write('\n\tMEAN:  {} seconds\n'.format(mean(PH)))
            f.write('\tSTDEV: {} seconds\n'.format(stdev(PH)))
            f.write('\tMIN:   {} seconds\n'.format(min(PH)))
            f.write('\tMAX:   {} seconds\n\n'.format(max(PH)))
        f.write('\nEF RESULTS:\n')
        for data in EF:
            f.write('\tRUN TIME [EF]: {} seconds\n'.format(data))
        else:
            f.write('\n\tMEAN:  {} seconds\n'.format(mean(EF)))
            f.write('\tSTDEV: {} seconds\n'.format(stdev(EF)))
            f.write('\tMIN:   {} seconds\n'.format(min(EF)))
            f.write('\tMAX:   {} seconds\n\n'.format(max(EF)))     
        
