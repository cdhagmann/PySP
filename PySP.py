from Crispin.bash import bash_command
from Crispin.context import temp_file
import Crispin.bash as bash
import time
from GBB import GBB


def mpath(mthd, archive):
    return 'models_{}/nodedata/{}.dat'.format(mthd, archive)

def nd_cat(mthd, nf, *ofs):
    new_file = mpath(mthd, nf)
    old_files = [mpath(mthd, of) for of in ofs]
    bash.cat(new_file, *old_files)

def parse_pysp_output(command, verbose):
    with temp_file() as temp:
        print '\n'.join(bash_command(command))

    if verbose:
        print command
        with open(temp, 'rb') as f:
            for line in f:
                print line

    with open(temp, 'rb') as f:
        for line in f:
            if 'THE EXPECTED SUM OF THE STAGE COST VARIABLES=' in line:
                OBJ = float(line.strip('<>\n').split('=')[-1])
                bash.rm(temp)
                break
            elif 'Cutoff' in line:
                OBJ = 'Cutoff Error'
                bash.rm(temp)
                break
        else:
            raise RuntimeError, temp

    return OBJ

def solve_ef(method='BigM', solver='gurobi', verbose=False):
    nd_cat(method, 'ScenarioStructure', 'ScenarioStructureBase', 'ScenarioStructureEF')

    cmd = ['runef',
           '-m models_{}/models'.format(method),
           '-i models_{}/nodedata'.format(method),
           '--solver={}'.format(solver),
           '--solve']

    basic_command = ' '.join(cmd)

    OBJ = parse_pysp_output(basic_command, verbose)

    return OBJ


def solve_ph(method='BigM', solver='gurobi', verbose=False, WW=False):
    nd_cat(method, 'ScenarioStructure', 'ScenarioStructureBase', 'ScenarioStructurePH')

    cmd = ['runph',
           '-m models_{}/models'.format(method),
           '-i models_{}/nodedata'.format(method),
           '--solver={}'.format(solver),
           '--default-rho=1',
           '--async']

    if WW:
        cmd += ['--enable-ww-extensions',
                '--ww-extension-cfgfile=config/wwph.cfg',
                '--ww-extension-suffixfile=config/wwph.suffixes']

    basic_command = ' '.join(cmd)

    OBJ = parse_pysp_output(basic_command, verbose)

    return OBJ

def RLT(method='PH', solver='gurobi', verbose=False):
    t1 = time.time()
    if method.upper() == 'PH':
        obj = solve_ph('RLT', solver, verbose)
    elif method.upper() == 'EF':
        obj = solve_ef('RLT', solver, verbose)
    t2 = time.time()

    return obj, t2 - t1

def BigM(method='PH', solver='gurobi', verbose=False):
    t1 = time.time()
    if method.upper() == 'PH':
        obj = solve_ph('BigM', solver, verbose)
    elif method.upper() == 'EF':
        obj = solve_ef('BigM', solver, verbose)
    t2 = time.time()

    return obj, t2 - t1

if '__main__' == __name__:
    T1 = GBB(cutoff=True, gap=.0175)
