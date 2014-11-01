import os
import subprocess
import glob
import fileinput
import sys

'''Print things to stdout on one line dynamically'''
class Printer():
    def __init__(self,data):
        sys.stdout.write("\r\x1b[K"+data.__str__())
        sys.stdout.flush()


'''Run BASH command in Python Script and return stdout as list.\n
   print '\n'.join(bash_command(command)) will properly display stdout to stdout'''
def bash_command(command):
    stdin,stdout = os.popen2(command)
    stdin.close()
    lines = stdout.readlines()
    stdout.close()
    lines = [line.strip('\n') for line in lines]
    return lines

'''Experimental Attempt to parallelized the bash command'''
sub_bash = lambda command: bash_command('gnome-terminal -x {} &\nwait'.format(command))

'''Concatenate files similiar to the BASH command cat.\n\n
   cat file1 file2 > file3 <---> cat_files(file3,[file1,file2])'''
def cat_files(name,filenames):
    command = 'cat {} > {}'.format(' '.join(filenames), name)
    return bash_command(command)   

''' Lazy shorthand for typing the string 'nodedata/{}.dat'.format(f)'''
fname = lambda f: 'nodedata/{}.dat'.format(f)


''' Generate the LP file for a given tech choice using the demand from the first scenari0.'''
def pyomo_lp(tech):
    filenames = [fname('RootNodeBase'),fname('Tech{}Node'.format(tech)),fname('Scenario1Node')]
    cat_files(fname('ReferenceModel'),filenames)
    command = 'pyomo --instance-only --symbolic-solver-labels --save-model=Tech{}.lp models/ReferenceModel.py nodedata/ReferenceModel.dat'.format(tech)
    print '\n'.join(bash_command(command))



''' Run EF on a problem and returns Objective value'''
def PySP_runef(solver='gurobi', verbose=False):
    command = 'runef --solve --solver={} --model-directory=models --instance-directory=nodedata'.format(solver)

    found = False
    
    lines = bash_command(command)
    if verbose:
        print '\n'.join(lines)
        
    for line in lines:
        if 'THE EXPECTED SUM OF THE STAGE COST VARIABLES=' in line:
            OBJ = float(line.strip('<>').split('=')[-1])
            return OBJ




''' Run the extentive form on each I x J subproblem and returns the best.'''    
def pyomo_runef(solver='gurobi', verbose=False):
    print "Initializing EF"
    filenames = [fname('ScenarioStructureBase'),fname('ScenarioStructureEF')]
    cat_files(fname('ScenarioStructure'),filenames) 
    Tech_Obj = {}
    flist  = glob.glob(fname('Tech*'))
    flist.sort()
    
    Total = len(flist)
      
    for idx,f in enumerate(flist):
        perc = (idx+1)/float(Total)
        tech = 'Tech{}'.format(idx)
        filenames = [fname('RootNodeBase'),f]
        cat_files(fname('RootNode'),filenames)
        
        Tech_Obj[tech] = PySP_runef(solver=solver, verbose=verbose)
        
        Printer("Finished {}: {} [{} Completed]".format(tech, Tech_Obj[tech], "{0:.2%}".format(perc)))
    else:
        print
        techs = [k for k in Tech_Obj]
        techs = sorted(techs, key=lambda tech: Tech_Obj[tech])
        print 'Optimial Choice: {} \nObjective Value: {}\n'.format(techs[0],Tech_Obj[techs[0]])



#########################################################################################


''' Run PH on a problem and returns Objective value'''
def PySP_runph(solver='gurobi', verbose=False):
    cmd = ['runph',
           '-m models',
           '-i nodedata',
           '--solver={}'.format(solver),
           '--default-rho=1',
           '--enable-ww-extensions',
           '--async']
           
    command = ' '.join(cmd)

    lines = bash_command(command)
    if verbose:
        print '\n'.join(lines)
        
    for line in lines:
        if 'THE EXPECTED SUM OF THE STAGE COST VARIABLES=' in line:
            OBJ = float(line.strip('<>').split('=')[-1])
            return OBJ




''' Run PH on each I x J subproblem and returns the best.'''          
def pyomo_runph(solver='gurobi', verbose=False):
    print "Initializing PH"
    filenames = [fname('ScenarioStructureBase'),fname('ScenarioStructurePH')]
    cat_files(fname('ScenarioStructure'),filenames)
    Tech_Obj = {}
    flist  = glob.glob(fname('Tech*'))
    flist.sort()
    Total = len(flist)
    
    for idx,f in enumerate(flist):
        perc = (idx+1)/float(Total)
        tech = 'Tech{}'.format(idx)
        filenames = [fname('RootNodeBase'),f]
        cat_files(fname('RootNode'),filenames)
        
        Tech_Obj[tech] = PySP_runph(solver=solver, verbose=verbose)
        
        Printer("Finished {}: {} [{} Completed]".format(tech, Tech_Obj[tech], "{0:.2%}".format(perc)))
    else:
        print
        techs = [k for k in Tech_Obj]
        techs = sorted(techs, key=lambda tech: Tech_Obj[tech])
        print 'Optimial Choice: {} \nObjective Value: {}\n'.format(techs[0],Tech_Obj[techs[0]])        

#########################################################################################
        
if __name__ == '__main__':
    pyomo_runph(verbose=True)
    pyomo_runef(verbose=True)
    
        
