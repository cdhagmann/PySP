import os, sys, shutil, glob, random, string


def id_generator(size=6):
    '''
    Generate a string of specified length size [default=6] of alpha-numeric
    characters.
    ''' 
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for x in range(size))
    
    
def bash_command(command, output=False):
    '''
    Run BASH command in Python Script and return stdout as list.
    '''
    stdin,stdout = os.popen2(command)
    stdin.close()
    lines = stdout.readlines()
    stdout.close()
    lines = [line.strip('\n') for line in lines]

    if output:
        print '\n'.join(lines)
        
    return lines


def ls(src=None):
    '''
    Show contents of src (similar to ls in UNIX). Takes '*' and '?' 
    '''
    i = 0
    src = '*' if src is None else src
    items = glob.glob(src)
    if items:
        N = max(map(len, items))
        M = int(80 / N)
        rows = [items[i:i + M] for i in range(0, len(items), M)]
        for row in rows:
            temp_string = ['{:{gap}}'] * len(row)
            print '\t'.join(temp_string).format(*row, gap=N)
            

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

def cat(new_file, *old_files):
    '''
    Concatenate files (similar to cat in UNIX).
    ''' 
    file_handle = 'temp{}'.format(id_generator(10))
    
    if len(old_files) == 1 and hasattr(old_files[0], '__iter__'):
        cat(new_file, *old_files[0])
    else:            
        with open(file_handle, 'wb') as f:
            for archive in old_files:
                assert os.path.isfile(archive), archive
                with open(archive, 'rb') as a:
                    for line in a:
                        f.write(line)
                    
    cp(file_handle, new_file)
    rm(file_handle)

        
cd = os.chdir
pwd = os.getcwd
