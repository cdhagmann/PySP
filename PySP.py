from Crispin.bash import bash_command
from Crispin.context import temp_file
import Crispin.bash as bash
import time
from GBB import GBB, parse_pysp_output


def mpath(mthd, archive):
    return 'models_{}/nodedata/{}.dat'.format(mthd, archive)

def nd_cat(mthd, nf, *ofs):
    new_file = mpath(mthd, nf)
    old_files = [mpath(mthd, of) for of in ofs]
    bash.cat(new_file, *old_files)


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
           '--async',
           '--output-solver-logs']

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
        results = solve_ph('RLT', solver, verbose)
    elif method.upper() == 'EF':
        results = solve_ef('RLT', solver, verbose)
    else:
        raise ValueError
    t2 = time.time()

    return results['obj'], t2 - t1

def BigM(method='PH', solver='gurobi', verbose=False):
    t1 = time.time()
    if method.upper() == 'PH':
        results = solve_ph('BigM', solver, verbose)
    elif method.upper() == 'EF':
        results = solve_ef('BigM', solver, verbose)
    else:
        raise ValueError
    t2 = time.time()

    return results['obj'], t2 - t1

if '__main__' == __name__:
    T1 = GBB(cutoff=True, gap=.0175)
