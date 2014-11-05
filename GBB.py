from Crispin.bash import bash_command
from Crispin.context import temp_file
import Crispin.bash as bash
import time
import glob
from Function_Module import perc, curr, ptime


def fname(archive):
    return 'models_GBB/nodedata/{}.dat'.format(archive)

def nd_cat(nf, *ofs):
    if len(ofs) == 1 and hasattr(ofs[0], '__iter__'):
        nd_cat(nf, *list(ofs[0]))
    else:
        new_file = fname(nf)
        old_files = [fname(of) for of in ofs]
        bash.cat(new_file, *old_files)


def solve_tech_model(idx, solver='gurobi', gap=None, cutoff=None, verbose=True):
    tech = 'Tech{}'.format(idx)
    nd_cat('RootNode', 'RootNodeBase', tech + 'Node')
    nd_cat('ScenarioStructure', 'ScenarioStructureBase', 'ScenarioStructureEF')

    cmd = ['runef',
           '-m models_GBB/models',
           '-i models_GBB/nodedata',
           '--solver={}'.format(solver),
           '--solve']

    basic_command = ' '.join(cmd)

    if gap is not None:
        basic_command += ' --solver-options=MIPGap={}'.format(gap)

    if cutoff is not None:
        basic_command += ' --solver-options=Cutoff={}'.format(cutoff)

    with temp_file() as temp:
        print '\n'.join(bash_command(basic_command + ' 2>/dev/null'))

    if verbose:
        print basic_command
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


def GBB(method='EF', solver='gurobi', gap=None, cutoff=True, verbose=False, output=False):
    assert method == 'EF'
    Times = []
    Techs = []
    Obj = []

    if cutoff is None:
        def cutoff_update(Obj):
            return None
    else:
        def cutoff_update(Obj):
            if Obj:
                return None if min(Obj) == float('inf') else min(Obj)
            else:
                return None

    total = len(glob.glob(fname('Tech*')))
    for idx in xrange(total):
        prog = (idx + 1.) / total
        tech = 'Tech{}'.format(idx)

        t1 = time.time()
        cutoff = cutoff_update(Obj)
        obj = solve_tech_model(idx, solver, gap, cutoff, verbose)
        t2 = time.time()
        T = t2 - t1

        Times.append(T)
        Techs.append(tech)


        if type(obj) == str:
            Obj.append(float('inf'))

            if min(Obj) == float('inf'):
                info = [tech, obj, obj, perc(prog), ptime(T)]
            else:
                info = [tech, obj, curr(min(Obj)), perc(prog), ptime(T)]
        else:
            Obj.append(obj)
            info = [tech, curr(obj), curr(min(Obj)), perc(prog), ptime(T)]

        if output:
            print "\tFinished {0:6}: {1:>12} ({2}) [{3:>7} Completed] ({4})".format(*info)

    else:
        OBJ = min(Obj)
        if OBJ == float('inf'):
            info = ['None', obj, ptime(sum(Times))]
        else:
            idx = Obj.index(OBJ)
            TECH = Techs[idx]
            info = [TECH, curr(OBJ), ptime(sum(Times))]

        return OBJ, sum(Times)


if '__main__' == __name__:
    T1 = GBB(cutoff=True, gap=.0175)
