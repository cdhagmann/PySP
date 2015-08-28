import time
import glob

import parse

from Crispin.bash import bash_command
import Crispin.bash as bash
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


def parse_pysp_output(command, verbose, solver_options=None, keep_log=True):
    log_file = 'gurobi.log'
    if isinstance(solver_options, dict) and solver_options:
        solver_options_string = ' '.join(['{}={}'.format(*entry) for entry in
                                          solver_options.iteritems()])

        command += ' --solver-options="{}"'.format(solver_options_string)

    # print command
    if verbose:
        print command + '\n\n'
        print '\n'.join(bash_command(command))
    else:
        bash_command(command)

    with open(log_file, 'rb') as glog:
        results = {}
        parser = None
        for line in glog:
            if 'Optimal solution found' in line:
                parser = 'Best objective {obj:e}, best bound {bound:e}, gap {gap:%}'
                results['status'] = 'optimal'
            elif 'Model objective exceeds cutoff' in line:
                parser = 'Best objective {}, best bound {bound:e}, gap {}'
                results['status'] = results['obj'] = 'Cutoff Error'
            elif 'status' in results:
                assert parser is not None
                result = parse.parse(parser, line.strip())
                results.update(**result.named)
                break
            else:
                pass


    bash.rm(log_file)

    return results


def solve_tech_model(idx, solver='gurobi', gap=None, cutoff=None, verbose=False):
    tech = 'Tech{}'.format(idx)

    nd_cat('RootNode', 'RootNodeBase', tech + 'Node')
    nd_cat('ScenarioStructure', 'ScenarioStructureBase', 'ScenarioStructureEF')

    cmd = ['runef',
           '-m models_GBB/models',
           '-i models_GBB/nodedata',
           '--solver={}'.format(solver),
           '--solve']

    # SET SOLVER OPTIONS
    solver_options = {}

    if gap is not None:
        solver_options['MIPGap'] = gap

    if cutoff is not None:
        solver_options['Cutoff'] = cutoff

    # COMPILE COMMAND
    command = ' '.join(cmd)

    results = parse_pysp_output(command, verbose, solver_options)

    if 'obj' in results:
        return results['obj']
    else:
        print results
        raise KeyError



def GBB(method='EF', solver='gurobi', gap=None, cutoff=True, verbose=False, output=True):
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
