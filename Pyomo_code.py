from Function_Module import *
from coopr.pyomo import *
from coopr import neos
from coopr.opt import SolverFactory
import coopr.environ
import os
import time
from PyomoCode.ReferenceTechModel import Pyomo_tech


def solve_tech_model(idx, solver='gurobi', time=None, gap=None, cutoff=None):
    tech = 'Tech{}'.format(idx)

    bash_command('rm -f ReferenceModel*')

    model = Pyomo_tech(idx)
    instance = model.create()
    # instance.write('model_{}.lp'.format(idx),symbolic_solver_labels=True)

    opt = SolverFactory(solver)
    if gap is not None:
        if gap < 1:
            opt.options["MIPGap"] = gap
        else:
            opt.options["MIPGapAbs"] = gap

    if time is not None:
        opt.options["TimeLimit"] = time

    if cutoff is not None:
        opt.options["Cutoff"] = cutoff

    with open('temp.log', 'w') as f:
        with Redirect(f, f):
            results = opt.solve(model, tee=True)

    status = results['Solver'][0]['Termination condition'].key

    transformed_results = instance.update_results(results)
    # print 'After Loading: {}'.format(status)
    if status == 'optimal':
        instance.load(results)
        rm('temp.log')
        obj = instance.Total_Cost_Objective()
        SubCost(tech, instance, obj)

        # FTI = [tech, instance.alpha_put.value, instance.alpha_pick.value]
        #print '\tFinished {0:6}: {1}, {2}'.format(*FTI)

        #FTI = [tech, instance.lambda_put.value/8., instance.lambda_pick.value/8.]
        #print '\tFinished {0:6}: {1:6} | {2:6}'.format(*FTI)       

        with open('results_{}.txt'.format(idx), 'w') as f:
            f.write('Results from {}\n'.format(tech))
            f.write('Putaway Technology: {}\n'.format(instance.lambda_put.value))
            f.write('Picking Technology: {}\n\n'.format(instance.lambda_pick.value))
            with Redirect(f, f):
                display(instance)

    else:
        obj = 'Cutoff Error'

    with open('results_{}.yml'.format(idx), 'w') as f:
        from check_sol import T

        f.write('Results from {}\n'.format(tech))
        f.write('Putaway Technology: {}\n'.format(T[idx][0]))
        f.write('Picking Technology: {}\n'.format(T[idx][1]))

        if status == 'optimal':
            f.write('Total_Cost_Objective:\n\tValue={}\n\n'.format(obj))
        else:
            f.write('Total_Cost_Objective:\n\tValue={}\n\n'.format(status))

        with Redirect(f, f):
            transformed_results.write()

    bash_command('rm -f ReferenceModel*')

    return tech, instance, obj


''' Run Pyomo on each I x J subproblem and returns the best.'''


def Pyomo_code(**kwargs):
    T_setup = 'gc.enable()\nfrom Pyomo_code import solve_tech_model'

    Times = []
    Techs = []
    Obj = []

    indices = sorted(reversed(range(36)), key=lambda k: k % 6, reverse=True)
    indices = kwargs.get('indices', indices)
    output = kwargs.get('output', True)
    cutoff = kwargs.get('cutoff', False)

    def T_command(idx, **kwargs):
        opts = {}
        time_limit = int( min([max( [P_timeout / len(indices), 2 * 3600] ), 12 * 3600]) )
        time_limit = 48 * 60 * 60 
        opts['S'] = kwargs.get('solver', 'gurobi')
        opts['T'] = kwargs.get('time', time_limit)
        opts['I'] = idx
        opts['G'] = kwargs.get('gap', None)

        if cutoff and Obj:
            if min(Obj) == float('inf'):
                opts['C'] = None
            else:
                if 0 <= opts['G'] < 1:
                    if min(Obj) * opts['G'] <= 1000:
                        opts['G'] = 1000
                        opts['C'] = min(Obj)  # + opts['G'] * 2
                    else:
                        opts['C'] = min(Obj)  # * (1 + 1.5 * opts['G'])
                else:
                    opts['C'] = min(Obj)  # + opts['G'] * 2

                opts['T'] = kwargs.get('time', min([max(Times) * 5000, time_limit]))
        else:
            opts['C'] = None

        args = "{I}, solver='{S}', time={T}, gap={G}, cutoff={C}".format(**opts)
        return 'solve_tech_model({})'.format(args)


    try:
        for i, idx in enumerate(indices):
            if i > 0:
                if sum(Times) + mean(Times) > P_timeout:
                    raise Exception

            prog = (i + 1) / float(len(indices))
            tech = 'Tech{}'.format(idx)

            # print 'Starting Tech {}'.format(idx)
            try:
                t1 = time.time()
                command = T_command(idx, **kwargs)
                # print command
                T = Timeit(command, setup=T_setup)
                obj = read_P_sol('results_{}.yml'.format(idx))
            except ValueError, e:
                print 'ValueError: ' + str(e)
            except Exception:
                t2 = time.time()
                T = t2 - t1

            Times.append(T)
            Techs.append(tech)

            if type(obj) == str:
                if obj == 'maxTimeLimit':
                    line = bash_command('tail -1 temp.log')[0]
                    obj = float(line.split()[2].strip(','))
                    err = float(line.split()[-1].strip('%'))
                    Obj.append(obj)
                    info = [tech, '{} [{}%]'.format(curr(obj), err), curr(min(Obj)), perc(prog), ptime(T)]
                else:    
                    Obj.append(float('inf'))
                
                    if min(Obj) == float('inf'):
                        info = [tech, obj, obj, perc(prog), ptime(T)]
                    else:
                        info = [tech, obj, curr(min(Obj)), perc(prog), ptime(T)]
            else:
                Obj.append(obj)
                info = [tech, curr(obj), curr(min(Obj)), perc(prog), ptime(T)]

            print "\tFinished {0:6}: {1} ({2}) [{3} Completed] ({4})".format(*info)

            with open('results_summary.txt', 'a') as f:
                f.write("Finished {0:6}: {1} ({2}) [{3} Completed] ({4})\n".format(*info))
    finally:
        print ''
        OBJ = min(Obj)
        if OBJ == float('inf'):
            info = ['None', obj, ptime(sum(Times))]
        else:
            idx = Obj.index(OBJ)
            TECH = Techs[idx]
            info = [TECH, curr(OBJ), ptime(sum(Times))]

            cp('results_{}.yml'.format(num_strip(TECH)), 'results_best.yml')
            cp('summary_{}.txt'.format(num_strip(TECH)), 'summary_best.txt')

        print "\tOptimal Solution {}: {} ({})".format(*info)
        with open('results_summary.txt', 'a') as f:
            f.write("\nOptimal Solution:\n\t{}: {} ({})".format(*info))

        command = 'rm -f ReferenceModel*'
        _ = bash_command(command)

        if output and not cutoff:
            L = zip(Techs, Obj)
            L.sort(key=lambda (t, o): o)
            print '\nTop 5 Techs:'
            for t, o in L[:5]:
                print '\t{0:6}: {1}'.format(t, curr(o))

        return OBJ, sum(Times)


P_timeout = 7 * 24 * 60 * 60

def read_P_sol(sol_file):
    with open(sol_file, 'r') as f:
        try:
            while 'Total_Cost_Objective' not in next(f):
                pass
            try:
                val = next(f).split('=')[1].strip()
                ans = float(val)
            except ValueError:
                if val == 'infeasible':
                    ans = 'Infeasible'
                elif val == 'minFunctionValue':
                    ans = 'Cutoff Error'
                else:
                    ans = val
        except StopIteration:
            ans = 'Unknown Error'
        finally:
            return ans


def tech_test(idx, t=None, gap=None):
    print time.strftime("%a, %d %b %Y %I:%M:%S %p")
    solve_tech_model(idx, time=t, gap=gap)
    print time.strftime("%a, %d %b %Y %I:%M:%S %p")


def SubCost(tech, inst, obj):
    idx = num_strip(tech)
    PickingCost = inst.C_alpha.value * inst.alpha_pick.value
    PickingCost += inst.C_beta.value * sum(inst.beta_pick[t].value for t in inst.TIMES)

    PutawayCost = inst.C_alpha.value * inst.alpha_put.value
    PutawayCost += inst.C_beta.value * sum(inst.beta_put[t].value for t in inst.TIMES)

    MHECost = sum(inst.MHE.value *
                  (inst.alpha_put.value + inst.beta_put[t].value) for t in inst.TIMES)

    PutawayTechCost = inst.C_put.value

    PickingTechCost = inst.C_pick.value

    WhBasicInvCost = sum(inst.C_hp[p] * inst.y_pt[p, t].value
                         for p in inst.PRODUCTS for t in inst.TIMES)

    WhFashionInvCost = sum(inst.C_hq[q] * inst.X_osq[s, q] * inst.tau_sq[s, q].value
                           for s in inst.STORES for q in inst.FASHION)

    StoreBasicInvCost = sum(inst.C_hsp[s, p] * inst.y_spt[s, p, t].value
                            for s in inst.STORES for p in inst.PRODUCTS for t in inst.TIMES)

    StoreFashionInvCost = sum(inst.C_hsq[s, q] * inst.y_sqt[s, q, t].value
                              for s in inst.STORES for q in inst.FASHION for t in inst.TIMES)

    BasicInbCost = sum(inst.C_fv[v] * inst.n_vt[v, t].value
                       for v in inst.VENDORS_P for t in inst.TIMES)
    BasicInbCost += sum(inst.C_vv[v] * inst.W_p[p] * inst.x_vpt[v, p, t].value
                        for v, p in inst.OMEGA_P for t in inst.TIMES)

    FashionInbCost = sum(inst.C_fv[v] * inst.n_vt[v, t].value
                         for v in inst.VENDORS_Q for t in inst.TIMES)
    FashionInbCost += sum(inst.C_vv[v] * inst.W_q[q] *
                          inst.X_ivq[v, q] * inst.rho_vqt[v, q, t].value
                          for v, q in inst.OMEGA_Q for t in inst.TIMES)

    OutboundCost = sum(inst.C_fs[s] * inst.n_st[s, t].value
                       for s in inst.STORES for t in inst.TIMES)
    OutboundCost += sum(inst.C_vs[s] * inst.W_p[p] * inst.x_spt[s, p, t].value
                        for s in inst.STORES for p in inst.PRODUCTS for t in inst.TIMES)
    OutboundCost += sum(inst.C_vs[s] * inst.W_q[q] *
                        inst.X_osq[s, q] * inst.rho_sqt[s, q, t].value
                        for s in inst.STORES for q in inst.FASHION for t in inst.TIMES)

    with open('summary_{}.txt'.format(idx), 'w') as f:
        from check_sol import T

        f.write('Results from {}\n'.format(tech))
        f.write('Putaway Technology: {}\n'.format(T[idx][0]))
        f.write('Picking Technology: {}\n\n'.format(T[idx][1]))
        f.write('Full-Time Putaway workers: {}\n'.format(inst.alpha_put.value))
        f.write('Full-Time Picking workers: {}\n'.format(inst.alpha_pick.value))
        f.write('\nCost Breakdown:\n')
        f.write('\tMHECost              {}\n'.format(curr(MHECost)))
        f.write('\tPutawayTechCost      {}\n'.format(curr(PutawayTechCost)))
        f.write('\tPickingTechCost      {}\n'.format(curr(PickingTechCost)))
        f.write('\tWhBasicInvCost       {}\n'.format(curr(WhBasicInvCost)))
        f.write('\tBasicInbCost         {}\n'.format(curr(BasicInbCost)))
        f.write('\tWhFashionInvCost     {}\n'.format(curr(WhFashionInvCost)))
        f.write('\tFashionInbCost       {}\n'.format(curr(FashionInbCost)))
        f.write('\tPutawayCost          {}\n'.format(curr(PutawayCost)))
        f.write('\tStoreBasicInvCost    {}\n'.format(curr(StoreBasicInvCost)))
        f.write('\tStoreFashionInvCost  {}\n'.format(curr(StoreFashionInvCost)))
        f.write('\tOutboundCost         {}\n'.format(curr(OutboundCost)))
        f.write('\tPickingCost          {}\n'.format(curr(PickingCost)))
        f.write('\tTotal                {}\n'.format(curr(obj)))
        with Redirect(f, f):
            print '\n\nPrinting New Fashion Solution:\n'
            ri = lambda num: int(round(num, 0))
            print 'Inbound Fashion Solution'
            for v, q in sorted(inst.OMEGA_Q):
                print num_strip(v), '\t',
                print num_strip(q), '\t',
                for t in sorted(inst.TIMES):
                    if inst.rho_vqt[v, q, t] == 1:
                        print t, '\t', ri(inst.X_ivq[v, q])

            print '\nOutbound Solution'
            for s in sorted(inst.STORES):
                for q in sorted(inst.FASHION):
                    print num_strip(s), '\t',
                    print num_strip(q), '\t',
                    for t in sorted(inst.TIMES):
                        if inst.rho_sqt[s, q, t] == 1:
                            print t, '\t', ri(inst.X_osq[s, q])

            print '\nStore Inventory'
            for s in sorted(inst.STORES):
                print 'Store{}'.format(num_strip(s))
                for q in sorted(inst.FASHION):
                    print num_strip(v),
                    for t in sorted(inst.TIMES):
                        num = ri(inst.y_sqt[s, q, t].value)
                        print str(num) + (' ' * (10 - len(str(num)))),
                    print

            print '\nShipments from (Basic) Vendor to Warehouse'
            for v in sorted(inst.VENDORS_Q):
                for t in sorted(inst.TIMES):
                    num = ri(inst.n_vt[v, t].value)
                    print str(num) + (' ' * (10 - len(str(num)))),
                print

            print '\nPrinting New Basic Solution:\n'

            print '\nInbound Solution'
            for v, p in sorted(inst.OMEGA_P):
                for t in sorted(inst.TIMES):
                    print num_strip(v), '\t',
                    print num_strip(p), '\t',
                    print t, '\t',
                    print ri(inst.x_vpt[v, p, t].value)

            print '\nOutbound Solution'
            for s in sorted(inst.STORES):
                print 'Store{}'.format(num_strip(s))
                for p in sorted(inst.PRODUCTS):
                    print num_strip(p),
                    for t in sorted(inst.TIMES):
                        num = ri(inst.x_spt[s, p, t].value)
                        print str(num) + (' ' * (10 - len(str(num)))),
                    print

            print '\nWarehouse Inventory'
            for p in sorted(inst.PRODUCTS):
                print num_strip(p),
                for t in sorted(inst.TIMES):
                    num = ri(inst.y_pt[p, t].value)
                    print str(num) + (' ' * (10 - len(str(num)))),
                print

            print '\nStore Inventory'
            for s in sorted(inst.STORES):
                print 'Store{}'.format(num_strip(s))
                for p in sorted(inst.PRODUCTS):
                    print num_strip(p),
                    for t in sorted(inst.TIMES):
                        num = ri(inst.y_spt[s, p, t].value)
                        print str(num) + (' ' * (10 - len(str(num)))),
                    print

            print '\nShipments from (Basic) Vendor to Warehouse'
            for v in sorted(inst.VENDORS_P):
                for t in sorted(inst.TIMES):
                    num = ri(inst.n_vt[v, t].value)
                    print str(num) + (' ' * (10 - len(str(num)))),
                print

            print '\nShipments from (Fashion) Vendor to Warehouse'
            for v in sorted(inst.VENDORS_Q):
                for t in sorted(inst.TIMES):
                    num = ri(inst.n_vt[v, t].value)
                    print str(num) + (' ' * (10 - len(str(num)))),
                print

            print '\nShipments from Warehouse to Stores'
            for s in sorted(inst.STORES):
                print num_strip(s),
                for t in sorted(inst.TIMES):
                    num = ri(inst.n_st[s, t].value)
                    print str(num) + (' ' * (10 - len(str(num)))),
                print

            print '\nNo of part-time putaway workers:'
            for t in sorted(inst.TIMES):
                num = ri(inst.beta_put[t].value)
                print str(num) + (' ' * (10 - len(str(num)))),
            print

            print '\nNo of part-time picking workers:'
            for t in sorted(inst.TIMES):
                num = ri(inst.beta_pick[t].value)
                print str(num) + (' ' * (10 - len(str(num)))),
            print


if '__main__' == __name__:
    T1 = Pyomo_code(cutoff=True, gap=.0175)
    # t, i, o = solve_tech_model(11)

    # SubCost(t,i,o)
    

