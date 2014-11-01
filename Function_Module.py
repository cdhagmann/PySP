import math
import multiprocessing as mp
import time, timeit
import string, random
import os, sys, shutil, glob
from contextlib import contextmanager


@contextmanager
def ignored(*exceptions):
    '''
    Can be used to replace
    
    try:
        code
    except Exception1, Exception2, ...:
        pass
        
    using
    
    with ignored(Exception1, Exception2, ...):
        code
    '''
    try:
        yield
    except exceptions:
        pass
    
     
#-----------------------------------------------------------------------------
#                          DEFINE TIMEOUT FUNCTION
#-----------------------------------------------------------------------------
        
def timeout(func, args=(), kwargs=None, TIMEOUT=10, default=None, err=.05):

    if hasattr(args, "__iter__") and not isinstance(args, basestring):
        args = args
    else:
        args = [args]    
    kwargs = {} if kwargs is None else kwargs

    pool = mp.Pool(processes = 1)

    try:
        result = pool.apply_async(func, args=args, kwds=kwargs)
        val = result.get(timeout = TIMEOUT * (1 + err))
    except mp.TimeoutError:
        pool.terminate()
        return default
    else:
        pool.close()
        pool.join()
        return val

def Timeit(command, setup=''):
    import timeit
    return timeit.Timer(command, setup=setup).timeit(1)
            
def timeit_timeout(command, setup='', TIMEOUT=10, default=None, err=.05):
    return timeout(Timeit, args=command, kwargs={'setup':setup},
                   TIMEOUT=TIMEOUT, default=default, err=err)
                   
#-----------------------------------------------------------------------------
#                          DEFINE USEFUL FUNCTION
#-----------------------------------------------------------------------------

''' Generates human readible CPU Times'''
def htime(s):
    if s < 60:
        H,M,S = 0,0,s
    elif s < 3600:
        H,M,S = 0, int(float(s) / 60), s % 60
    else:
        S = s % 60
        s -= S
        
        H = int(float(s) / 3600)
        s -= float(H) * 3600
        
        M = int(float(s) / 60)
        s -= float(M) * 60

        assert s < 1
        
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


def pretty_string(string, t=None, n=None, to_write=False):
    if n is None:
        suf = '\n' if to_write else ''
    else:
        suf = ( (n + 1) if to_write else n ) * '\n'

    pre = '' if t is None else (' ' * 4) * t

    return pre + string + suf  

def qprint(string, t=None, n=None):
    print pretty_string(string, t, n)
    
def qwrite(filename, string, t=None, n=None):
    string = pretty_string(string, t, n, to_write=True)
    
    if type(filename) == str:
        with open(filename, 'a') as f:
            f.write(string)
    elif type(filename) == file:
        filename.write(string)
    else:
        filename = str(filename)
        with open(filename, 'a') as f:
            f.write(string)
  
       
'''Print to STDOUT and to the file.'''   
def tee_print(filename,string, t=None, n=None):
    qprint(          string, t, n)
    qwrite(filename, string, t, n)
        
def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for x in range(size))

'''Run BASH command in Python Script and return stdout as list.'''
def bash_command(command, output=False):
    stdin,stdout = os.popen2(command)
    stdin.close()
    lines = stdout.readlines()
    stdout.close()
    lines = [line.strip('\n') for line in lines]

    if output:
        print '\n'.join(lines)
        
    return lines




def cp(src, dst):
    '''
    Copy files to dst (similar to cp in UNIX). Takes '*' and '?'
    ''' 
    for f in glob.iglob(src):
        shutil.copy2(f, dst)


def rm(src):
    '''
    Remove files and directories (similar to rm -r in UNIX). Takes '*' and '?'. 
    ''' 
    for f in glob.iglob(src):
        if os.path.isfile(f):
            os.remove(f)
        elif os.path.isdir(f):
            shutil.rmtree(f)


def mv(src, dst):
    '''
    Move files and directories (similar to mv in UNIX). Takes '*' and '?'. 
    ''' 
    for f in glob.iglob(src):
        cp(f, dst)
        rm(f)







class Printer():
    def __init__(self,data):
        sys.stdout.write("\r\x1b[K"+data.__str__())
        sys.stdout.flush()

def num_strip(s):
    return int( ''.join( c for c in str(s) if c.isdigit() ) )

def var_round(num, n=16):
    assert isinstance(num, (float, int))

    for i in xrange(n):
        a, b, c = round(num, i), round(num, i + 1), round(num, i + 2)
        if a == b == c:
            break

    return int(b) if int(b) == b else b
   
class Redirect(object):
    def __init__(self, stdout=None, stderr=None):
        self._stdout = stdout or sys.stdout
        self._stderr = stderr or sys.stderr

    def __enter__(self):
        self.old_stdout, self.old_stderr = sys.stdout, sys.stderr
        self.old_stdout.flush(); self.old_stderr.flush()
        sys.stdout, sys.stderr = self._stdout, self._stderr

    def __exit__(self, exc_type, exc_value, traceback):
        self._stdout.flush(); self._stderr.flush()
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr

devnull = open(os.devnull, 'w')

suppress = Redirect(stdout=devnull, stderr=devnull)

class Printer():
    def __init__(self,data):
        sys.stdout.write("\r\x1b[K"+data.__str__())
        sys.stdout.flush()

mean = lambda l: sum(l)/float(len(l)) if l else 'N/A'
perc = lambda num: "{0:.2%}".format(float(num))

stdev = lambda s: math.sqrt(mean(map(lambda x: (x - mean(s))**2, s)))
perr = lambda part, whole: perc(part/float(whole))
line = lambda c,n: str(c * n)

def argmin(A):
    O = min(A)
    I = A.index(O)
    return O, I
    
def argmax(A):
    O = max(A)
    I = A.index(O)
    return O, I

class Struct():
    pass


path = lambda *args: '/'.join(map(str,args))
mkpath = lambda path: bash_command('mkdir -p ' + path)

def Timer(func):
    def _inner(*args, **kwargs):
        T1 = time.time()
        Results = func(*args, **kwargs)
        T2 = time.time()
        return Results, T2 - T1
    return _inner

      
class OrderedSet(list):
    def __init__(self, iterable=None):
        list.__init__(self)
        if iterable is not None:
            assert hasattr(iterable, '__iter__')
            
            for item in iterable:
                self.append(item)
            
    def append(self, item):
        if item not in self:
            list.append(self, item)





    
#-----------------------------------------------------------------------------
#                          DEFINE CURRENCY FUNCTION
#-----------------------------------------------------------------------------

import decimal

# http://stackoverflow.com/questions/17113996/how-can-i-print-any-float-like-1-234e22-in-a-long-nicely-rounded-and-localize/17116612#17116612
num = 1.23456E22
num2 = 1.23456E-22

group_frac = True

# http://stackoverflow.com/questions/2663612/nicely-representing-a-floating-point-number-in-python/2663623#2663623
def float_to_decimal(f):
    # http://docs.python.org/library/decimal.html#decimal-faq
    "Convert a floating point number to a Decimal with no loss of information"
    n, d = f.as_integer_ratio()
    numerator, denominator = decimal.Decimal(n), decimal.Decimal(d)
    ctx = decimal.Context(prec=60)
    result = ctx.divide(numerator, denominator)
    while ctx.flags[decimal.Inexact]:
        ctx.flags[decimal.Inexact] = False
        ctx.prec *= 2
        result = ctx.divide(numerator, denominator)
    return result 

def f(number, sigfig):
    assert( sigfig > 0 )

    try:
        d = decimal.Decimal(number)
    except TypeError:
        d = float_to_decimal(float(number))

    sign, digits, exponent = d.as_tuple()
    
    if len(digits) < sigfig:
        digits = list(digits)
        digits.extend([0] * (sigfig - len(digits)))    
    shift=d.adjusted()
    result=int(''.join(map(str,digits[:sigfig])))
    # Round the result
    if len(digits)>sigfig and digits[sigfig]>=5: result+=1
    result=list(str(result))
    # Rounding can change the length of result
    # If so, adjust shift
    shift+=len(result)-sigfig
    # reset len of result to sigfig
    result=result[:sigfig]
    if shift >= sigfig-1:
        # Tack more zeros on the end
        result+=['0']*(shift-sigfig+1)
    elif 0<=shift:
        # Place the decimal point in between digits
        result.insert(shift+1,'.')
    else:
        # Tack zeros on the front
        assert(shift<0)
        result=['0.']+['0']*(-shift-1)+result
    if sign:
        result.insert(0,'-')
    return ''.join(result)

def magic_format(num, group_frac=True):
    sep = ','
    dec = '.'

    n = float(('%E' % num)[:-4:])
    sigfig = len(str(n)) - (1 if '.' in str(n) else 0) 

    s = '{0:.2f}'.format(float(f(num,sigfig)))

    if group_frac:
        ans = ""
        if '.' not in s:
            point = None
            new_d = ""
            new_s = s[::-1]
        else:
            point = s.index('.')
            new_d = s[point+1::]
            new_d += max([0, 2 - len(new_d)]) * '0'
            new_s = s[:point:][::-1]
        for idx,char in enumerate(new_d):
            ans += char
            if (idx+1)%3 == 0 and (idx+1) != len(new_d): 
                ans += sep
        else: ans = ans[::-1] + (dec if point != None else '')
        for idx,char in enumerate(new_s):
            ans += char
            if (idx+1)%3 == 0 and (idx+1) != len(new_s): 
                ans += sep 
        else:
            ans = ans[::-1]
    else:
        ans = s
    return ans

def curr(val):
    s_val = magic_format(abs(val))
    return '${}'.format(s_val) if val >= 0 else '-${}'.format(s_val)
    

                           
