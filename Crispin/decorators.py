import time
from ProgressBar import ProgressBar
import functools

def Cache(func):
    '''
    Create a cache of previous executions for faster exectution of previously
    calculated values.
    
    @Cache
    def func(*args, **kwargs):
        ##Complex and time consuming code
        
    func(*args, **kwargs) # func is executed and results are returned
    func(*args, **kwargs) # func is NOT executed and results are returned from cache
    '''
    @functools.wraps(func)
    def __inner(*args, **kwargs):
        key = tuple(args + sorted( kwargs.items() ))
        func.cache = getattr(func, 'cache', {})
        if key not in func.cache:
            func.cache[key] = func(*args)
        return func.cache[key]
    return __inner
    

def Timer(func):
    '''
    Time every call of the function.
    
    @Timer
    def func(*args, **kwargs):
        ##Complex and time consuming code
        
    Results, run_time = func(*args, **kwargs)
    ''' 
    @functools.wraps(func)
    def __inner(*args, **kwargs):
        t1 = time.time()
        ans = func(*args, **kwargs)
        t2 = time.time()
        return ans, t2 - t1
    return __inner

if "__main__" == __name__:   
    @Cache    
    def RP(a, b):
        ans = 0
        while a > 0:
            if a%2 == 1:
                ans += b
            a, b = a >> 1, b << 1
        return ans        

    
    def Russian_Peasant(a, b):
        key = (a, b) if a < b else (b, a)
        return RP(*key)                               
    
    
    @Timer    
    def Product(*args):
        if len(args) == 1:
            if isinstance(args[0], (list, tuple)):
                return P(*args[0])
            else:
                return args[0]
        else:
            return Russian_Peasant(args[0], Product(args[1:]))

    

    
