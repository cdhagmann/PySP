import sys, os, time
from contextlib import contextmanager
from bash import id_generator

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
        

@contextmanager
def Redirect(filename, mode='w'):
    '''
    Redirect output from stdout and stderr to a file
    
    with Redirect('foo.txt', 'w'):
        print 'Hello'
        print 'World'
        
    would yield the same results as
    
    with open('foo.txt', 'w') as f:
        f.write('Hello' + \\n)
        f.write('World')
        
    Most useful when some function call prints to stdout and doesn't give the
    option to pipe to a file.
    
    def foo():
        print 'Hello World'
        
    with Redirect('foo.txt', 'w'):
        foo()
    '''
    old_stdout, old_stderr = sys.stdout, sys.stderr
    with open(filename, mode) as f:
        sys.stdout, sys.stderr = f, f
        yield
    sys.stdout, sys.stderr = old_stdout, old_stderr


@contextmanager
def suppression():
    '''
    Suppress output to stdout and stderr
    
    with suppression():
        print 'Hello, world!'
        
    # nothing prints
    '''
    with Redirect(os.devnull):
        yield


@contextmanager
def temp_file():
    '''
    Redirect output to temporary file
    
    with temp_file() as temp:
        foo()
    '''
    file_handle = 'temp{}'.format(id_generator(10))
    with Redirect(file_handle):
        yield file_handle

        
@contextmanager
def wait_until(string, format=None):
    '''
    Wait to execute code until the specified time. Takes the following
    formats or you can specified your specific format:
    
    8:00 PM           ['%I:%M %p']
    8:00:00 AM        ['%I:%M:%S %p']
    Friday 8:00 AM    ['%A %I:%M %p']
    Friday 8:00:00 PM ['%A %I:%M:%s %p']
    Thu 8:00 AM       ['%a %I:%M %p']
    Tue 8:00:00 PM    ['%a %I:%M:%S %p']
    
    with wait_until(8:00 AM):
        cook_spam()
    
    with wait_until(Friday 12:00 PM):
        push_pram('a lot')
    '''        
    formats = ['%I:%M %p', '%I:%M:%S %p',
               '%A %I:%M %p', '%A %I:%M:%S %p',
               '%a %I:%M %p', '%a %I:%M:%S %p']
    
    if format is not None:
        formats.insert(0, format)
        
    for format in formats:                       
        with ignored(ValueError):
            then = time.strptime(string, format)
            break
            
    foo = time.strftime(format, time.localtime())
    now = time.strptime(foo, format)
    
    NOW = (now.tm_wday, now.tm_hour, now.tm_min, now.tm_sec)
    THEN = (then.tm_wday, then.tm_hour, then.tm_min, then.tm_sec)   
    
    minutes = 60
    hours = 60 * minutes
    days = 24 * hours
            
    _to_int = lambda (w, h, m, s): w * days + h * hours + m * minutes + s
    
    bar = _to_int(THEN) - _to_int(NOW)
    if bar < 0:
        if bar > -1 * days:
            bar += 1 * days
        elif bar > -7 * days:
            bar += 7 * days
        else:
            raise ValueError
            
    time.sleep(bar)
    yield    
