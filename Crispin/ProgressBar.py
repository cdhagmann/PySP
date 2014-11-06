import time, threading, random, sys, functools

class Printer():
    def __init__(self,data):
        sys.stdout.write("\r\x1b[K"+data.__str__())
        sys.stdout.flush()


class func_thread(threading.Thread):
    def __init__(self,callback, func):
        self.callback = callback
        self.killed = False
        self.func = func
        threading.Thread.__init__(self)
    
    
    def Kill(self):
        self.killed = True
        print

    
    def run(self):
        while not self.killed:
            self.callback(self.func())


class Progressbar(object):
    def __init__(self, done_time, update_interval=.001, N=60, rotate=True):
        self.done_time = done_time
        self.update_interval = update_interval
        self.N = N
        self.rotate = rotate

        
    def progress(self, perc, count={}):
        perc = min( [perc, 1] )
        
        P = perc * self.N
        I = int( P )
        
        char = {0:'\\', 1:'|', 2:'/', 3:'-'}
        count['char'] = count.get('char', 0)
        bar = I * '#' + (char[count['char']%4] if perc < 1 and self.rotate else '')
        count['char'] += 1
        info = ( bar , self.N, perc )
        Printer('[{0:{1}}] {2:.0%} Finished'.format(*info) )        

    
    def start(self, func):
        my_results = []
        fs = func_thread(my_results.append, func)

        try:    
            fs.start()
            start_time = time.time()    
            delta_t = lambda: (time.time() - start_time) / self.done_time
            while delta_t() <= 1:
                 self.progress( delta_t() ) 
                 time.sleep( self.update_interval )
            self.progress( delta_t() )
        except KeyboardInterrupt:
            fs.Kill()
            fs.join()
        except Exception as e:
            print e
            fs.Kill()
            fs.join()
            
        fs.Kill()
        fs.join()
        return my_results         


def ProgressBar(done_time, update_interval=.25, N=50, rotate=True):
    def wrap(f):
        foo = Progressbar(done_time, update_interval, N, rotate)
        @functools.wraps(f)
        def wrapped_f(*args):
            my_results = foo.start(f)
            return my_results
        return wrapped_f
    return wrap

            
if __name__ == '__main__':
    @ProgressBar(250)
    def func():
        R = random.uniform(0.5,2.0)
        time.sleep(R)
        return R
        
    for _ in xrange(3):    
        my_results = func()
        print "DONE FINAL COUNT:",len(my_results)

