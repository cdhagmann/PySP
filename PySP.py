from Crispin.bash import bash_command
from Crispin.context import temp_file
import Crispin.bash as bash

def nd_cat(nf, *ofs):
    if len(ofs) == 1 and hasattr(ofs[0], '__iter__'):
        nd_cat(nf, *list(ofs[0]))
    else:
        new_file = 'nodedata/{}.dat'.format(nf)
        old_files = ['nodedata/{}.dat'.format(of) for of in ofs]
        bash.cat(new_file, *old_files)

def parse_pysp_output(command, verbose):
    with temp_file() as temp:
        print '\n'.join(bash_command(command))

    if verbose:
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


def solve_ef_tech_model(idx, method='GBB', solver='gurobi',
                             gap=None, cutoff=None, verbose=True):

    if method == 'GBB':
        tech = 'Tech{}'.format(idx)
        nd_cat('RootNode', 'RootNodeBase', tech + 'Node')
    else:
        tech = None    
    nd_cat('ScenarioStructure', 'ScenarioStructureBase', 'ScenarioStructureEF')

    cmd = ['runef',
           '-m models_{}/models'.format(method),
           '-i models_{}/nodedata'.format(method),
           '--solver={}'.format(solver),
           '--solve']

    basic_command = ' '.join(cmd)

    if gap is not None:
        basic_command += ' --solver-options=MIPGap={}'.format(gap)

    if cutoff is not None:
        basic_command += ' --solver-options=Cutoff={}'.format(cutoff)

    print basic_command
    OBJ = parse_pysp_output(basic_command, verbose)

    return tech, None, OBJ


def solve_ph_tech_model(idx, method='BigM', solver='gurobi', verbose=True, WW=False):
    tech = 'Tech{}'.format(idx)
    nd_cat('RootNode', 'RootNodeBase', tech + 'Node')
    nd_cat('ScenarioStructure', 'ScenarioStructureBase', 'ScenarioStructurePH')

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

    print basic_command
    OBJ = parse_pysp_output(basic_command, verbose)

    return tech, None, OBJ
