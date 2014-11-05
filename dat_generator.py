import random
import itertools
import pdat
import sys
import os
import fileinput
import shutil
import pickle

def randomize(number, stdev=.1):
    random_load = random.normalvariate(number, stdev * number)
    return int(max([0, round(random_load, 0)]))

def scale(lower_bound, upper_bound, number):
    gen = (1. * n / (number - 1) for n in xrange(number))
    return [lower_bound + (upper_bound - lower_bound) * g for g in gen]


class Struct():
    pass


def cat_files(name, filenames):
    with open(name, 'w') as f:
        for line in fileinput.input(filenames):
            f.write(line)


def dat_generator(S, V, P, I, J, T, K, seed=None):
    HPT = 8
    TPY = 28

    if seed is None:
        seed = round(1000 * random.random(), 2)

    random.seed(seed)

    DATA = Struct()

    DATA.STORES = ["s" + str(s + 1) for s in xrange(S)]
    DATA.VENDORS = ["v" + str(v + 1) for v in xrange(V)]
    DATA.PRODUCTS = ["p" + str(p + 1) for p in xrange(P)]
    DATA.PUTAWAY = ["i" + str(i + 1) for i in xrange(I)]
    DATA.PICKING = ["j" + str(j + 1) for j in xrange(J)]
    DATA.TIMES = [str(t + 1) for t in xrange(T)]
    DATA.SCENARIOS = ["k" + str(k + 1) for k in xrange(K)]

    DATA.case = ','.join(map(str, (S, V, P, I, J, T, K)))

    FT_HOURLY = random.randint(25, 40)
    PT_HOURLY = random.randint(20, min([FT_HOURLY - 1, 30]))

    DATA.C_ALPHA = FT_HOURLY * HPT * T
    DATA.C_BETA = FT_HOURLY * HPT


    # Generate various sensitivity parameters
    DATA.GAMMA = 1.0
    DATA.DELTA = 1.0
    DATA.ETA = 1.0

    # Generate volume of the truck
    DATA.SCRIPTQ = 15000

    # Generate workload parameters
    DATA.AVERAGE_LOAD = min([4000. / P, 50])

    # Generate product characteristics (Volume and Weight)
    DATA.VOLUME, DATA.WEIGHT = {}, {}
    for p in DATA.PRODUCTS:
        DATA.VOLUME[p] = round(random.random() * .1 + .01, 2)
        DATA.WEIGHT[p] = round(random.random() * .1 + .90, 2)


    # Generate cost of various technologies
    DATA.TECH_COST, DATA.LAMBDA = {}, {}

    RATE_SCALE = scale(4800, 48000, I)
    COST_SCALE = scale(0, .06, I)

    for i, t in enumerate(DATA.PUTAWAY):
        DATA.LAMBDA[t] = randomize(RATE_SCALE[i])
        DATA.TECH_COST[t] = randomize(DATA.LAMBDA[t] * COST_SCALE[i])

    RATE_SCALE = scale(800, 8000, J)
    COST_SCALE = scale(.03, .15, J)

    for i, t in enumerate(DATA.PICKING):
        DATA.LAMBDA[t] = randomize(RATE_SCALE[i])
        DATA.TECH_COST[t] = randomize(DATA.LAMBDA[t] * COST_SCALE[i])

    DATA.Lambda_put = {i: DATA.LAMBDA[i] for i in DATA.PUTAWAY}
    DATA.Lambda_pick = {j: DATA.LAMBDA[j] for j in DATA.PICKING}

    DATA.DEMAND = {}
    for s in DATA.STORES:
        for p in DATA.PRODUCTS:
            mu = randomize(DATA.AVERAGE_LOAD, .4)
            for t in DATA.TIMES:
                demands = sorted([randomize(mu, .25) for _ in xrange(K)])
                demands.sort()
                mu = random.choice(demands)
                for k, d in zip(DATA.SCENARIOS, demands):
                    DATA.DEMAND[s, p, t, k] = d

    temp = []
    for s in DATA.STORES:
        for p in DATA.PRODUCTS:
            for k in DATA.SCENARIOS:
                temp.append(sum(DATA.DEMAND[s, p, t, k] for t in DATA.TIMES))
    DATA.BigM = int(max(temp) + 1)
    # Data for holding cost for product p at the warehouse
    DATA.Cz = {}
    for p in DATA.PRODUCTS:
        DATA.Cz[p] = .05
    for s, p in itertools.product(DATA.STORES, DATA.PRODUCTS):
        DATA.Cz[s, p] = .05

    # Data for backlog cost for product p at store s
    DATA.Cr = {p: .10 for p in DATA.PRODUCTS}

    #-------------------------------------------------------------------
    #                  GENERATE TRANSPORTATION COSTS
    #-------------------------------------------------------------------

    TransportDataA = [25, 50, 75, 100, 150,
                      200, 250, 300, 350, 400,
                      500, 600, 700, 800, 900, 1000, 1100]

    TransportDataB = [40.42, 45.59, 52.27, 66.13, 75.28,
                      85.67, 97.5, 110.96, 126.26, 143.71,
                      186.09, 217.05, 253.17, 297.11, 344.43, 401.77, 468.61]

    TransportDataC = [427.6, 441.14, 482.83, 492.45, 521.43,
                      541.39, 570.02, 598.03, 622.3, 659.96,
                      727.61, 802.19, 884.41, 975.07, 1075.01, 1185.2, 1306.68]

    TransportDataD = [0.022, 0.027, 0.029, 0.034, 0.036,
                      0.041, 0.042, 0.045, 0.047, 0.05,
                      0.055, 0.061, 0.067, 0.074, 0.081, 0.09, 0.099]

    DistanceInMiles = TransportDataA
    FixedCost = dict(zip(TransportDataA, TransportDataB))
    Variable_Fixed = dict(zip(TransportDataA, TransportDataC))
    Variable = dict(zip(TransportDataA, TransportDataD))

    dist_VW, dist_WS, Cf, Cv, Cvf = {}, {}, {}, {}, {}

    dist_subset = [x for x in DistanceInMiles if x >= 250]
    for v in DATA.VENDORS:
        dist_VW[v] = random.choice(dist_subset)
        Cf[v] = FixedCost[dist_VW[v]]
        Cvf[v] = Variable_Fixed[dist_VW[v]]
        Cv[v] = Variable[dist_VW[v]]

    for s in DATA.STORES:
        rnd_num = random.random()
        if rnd_num <= .4:
            dist_subset = [x for x in DistanceInMiles if x <= 300]
        elif .4 < rnd_num <= .7:
            dist_subset = [x for x in DistanceInMiles if 300 <= x <= 800]
        else:
            dist_subset = DistanceInMiles

        dist_WS[s] = random.choice(dist_subset)
        Cf[s] = FixedCost[dist_WS[s]]
        Cv[s] = Variable[dist_WS[s]]
        Cvf[s] = Variable_Fixed[dist_WS[s]]

    DATA.Cv_s = {s: Cv[s] for s in DATA.STORES}
    DATA.Cf_v = {v: Cvf[v] + Cf[v] for v in DATA.VENDORS}
    DATA.Cf_s = {s: Cvf[s] + Cf[s] for s in DATA.STORES}
    DATA.Cv_v = {v: Cv[v] for v in DATA.VENDORS}

    #-------------------------------------------------------------------
    #               GENERATE PROBABILITIES IF NOT PROVIDED
    #-------------------------------------------------------------------

    DATA.prob = {k: 1.0 / K for k in DATA.SCENARIOS}


    with open('Instances/Pickled_Data_{:.0f}'.format(seed * 100), 'wb') as f:
        pickle.dump(DATA, f, protocol=-1)

    print "Pickled Data"

    return DATA

def create_nodedata(data, method=None):
    if isinstance(data, str):
        data = pickle.load(data)

    if method is None:
        methods = ('GBB', 'RLT', 'BigM')
    elif isinstance(method, (list, tuple)):
        for mthd in method:
            assert mthd in ('GBB', 'RLT', 'BigM')
        methods = tuple(method)
    elif isinstance(method, str):
        assert method in ('GBB', 'RLT', 'BigM')
        methods = (method,)

    for mthd in methods:
        shutil.rmtree('{}/nodedata'.format(mthd))
        os.mkdir('{}/nodedata'.format(mthd))

        def fname(archive): return '{}/nodedata/{}.dat'.format(mthd, archive)

        with open(fname('RootNodeBase'), 'w') as f:
            f.write('# Case of size [{}]\n\n'.format(data.case))

            pdat.set_dat(f, 'STORES', data.STORES)
            pdat.set_dat(f, 'PRODUCTS', data.PRODUCTS)
            pdat.set_dat(f, 'VENDORS', data.VENDORS)
            pdat.set_dat(f, 'TIMES', data.TIMES)
            if mthd in ('RLT', 'BigM'):
                pdat.set_dat(f, 'PUTAWAY', data.PUTAWAY)
                pdat.set_dat(f, 'PICKING', data.PICKING)

            if mthd == 'GBB':
                IJ = list(itertools.product(data.PUTAWAY, data.PICKING))

                for idx, (i, j) in enumerate(IJ):
                    file_name = 'Tech{}Node'.format(idx)
                    with open(fname(file_name), 'w') as f:
                        pdat.param_dat(f, 'PutawayRate', data.Lambda_put[i])
                        pdat.param_dat(f, 'PickingRate', data.Lambda_pick[j])
                        pdat.param_dat(f, 'PutawayTechCost', data.Cth_put[i])
                        pdat.param_dat(f, 'PickingTechCost', data.Cth_pick[j])
            else:
                pdat.param_dat(f, 'Lambda_put', data.Lambda_put, data.PUTAWAY)
                pdat.param_dat(f, 'Lambda_pick', data.Lambda_pick, data.PICKING)
                pdat.param_dat(f, 'Cth_put', data.Cth_put, data.PUTAWAY)
                pdat.param_dat(f, 'Cth_pick', data.Cth_pick, data.PICKING)

            pdat.param_dat(f, 'A_put', data.AVERAGE_LOAD)
            pdat.param_dat(f, 'A_pick', data.AVERAGE_LOAD)

            pdat.param_dat(f, 'gamma', data.GAMMA)
            pdat.param_dat(f, 'delta', data.DELTA)

            pdat.param_dat(f, 'eta_put', data.ETA)
            pdat.param_dat(f, 'eta_pick', data.ETA)

            pdat.param_dat(f, 'ScriptQ', data.SCRIPTQ)
            pdat.param_dat(f, 'V_p', data.VOLUME, data.PRODUCTS)
            pdat.param_dat(f, 'W_p', data.WEIGHT, data.PRODUCTS)

            pdat.param_dat(f, 'Cf_v', data.Cf_v, data.VENDORS)
            pdat.param_dat(f, 'Cv_v', data.Cv_v, data.VENDORS)
            pdat.param_dat(f, 'Cf_s', data.Cf_s, data.STORES)
            pdat.param_dat(f, 'Cv_s', data.Cv_s, data.STORES)

            pdat.param_dat(f, 'Cz_p', data.Cz, data.PRODUCTS)
            pdat.param_dat(f, 'Cz_sp', data.Cz, [data.STORES, data.PRODUCTS])

            pdat.param_dat(f, 'Cr_p', data.Cr, data.PRODUCTS)

            pdat.param_dat(f, 'Ca', data.C_ALPHA)
            pdat.param_dat(f, 'Cb', data.C_BETA)

            if mthd == 'GBB':
                pass
            elif mthd == 'RLT':
                pdat.param_dat(f, 'M_aplha', 200)
                pdat.param_dat(f, 'M_beta', 200)
            else:
                pdat.param_dat(f, 'BigM', data.BigM)


    for idx, k in enumerate(data.SCENARIOS):
        file_name = 'Scenario{}Node'.format(idx+1)
        with open(fname(file_name), 'w') as f:
            f.write('# Demand data for Scenario {}\n\n'.format(idx + 1))
            f.write('param Demand :=\n')
            spt = itertools.product(data.STORES, data.PRODUCTS, data.TIMES)
            for s, p, t in spt:
                info = (' '.join([s, p, t]), data.DEMAND[s, p, t, k])
                f.write('{} {}\n'.format(*info))
            f.write(';\n\n')

    # Create reference files for checks
    filenames = [fname('RootNodeBase'), fname('Tech0Node')]
    cat_files(fname('RootNode'), filenames)

    filenames = [fname('RootNode'), fname('Scenario1Node')]
    cat_files(fname('ReferenceModel'), filenames)

    # Create the base of the ScenarioStructure file
    with open(fname('ScenarioStructureBase'), 'w') as f:
        stages = ['FirstStage', 'SecondStage']

        scenarionodes = []
        p = {'RootNode': 1}
        NodeStage = {'RootNode': 'FirstStage'}
        for idx, k in enumerate(data.SCENARIOS, 1):
            scenario_node = 'Scenario{}Node'.format(idx)
            scenarionodes.append(scenario_node)
            p[scenario_node] = data.prob[k]
            NodeStage[scenario_node] = 'SecondStage'

        nodes = ['RootNode'] + scenarionodes
        StageCostVariable = {stage:'{}Cost'.format(stage) for stage in stages}

        ScenarioLeafNode = dict(zip(data.SCENARIOS, scenarionodes))


        FirstStageVariables = ['alpha_put',
                               'alpha_pick']

        if mthd in ('RLT', 'BigM'):
            FirstStageVariables += ['theta_put[*]',
                                    'theta_pick[*]']

        if mthd == 'RLT':
            FirstStageVariables += ['zeta_put[*]',
                                    'zeta_pick[*]']

        SecondStageVariables = ['beta_put[*]',
                                'beta_pick[*]',
                                'n_vt[*,*]',
                                'n_st[*,*]',
                                'x_vpt[*,*,*]',
                                'y_spt[*,*,*]',
                                'z_pt[*,*]',
                                'z_spt[*,*,*]',
                                'r_spt[*,*,*]']

        if mthd == 'RLT':
            SecondStageVariables = ['xi_put[*,*]',
                                    'xi_pick[*]']

        pdat.set_dat(f, 'Stages', stages)
        pdat.set_dat(f, 'Nodes', nodes)

        pdat.param_dat(f, 'NodeStage', NodeStage, nodes)
        pdat.set_dat(f, 'Children[RootNode]', scenarionodes)
        pdat.param_dat(f, 'ConditionalProbability', p, nodes)
        pdat.set_dat(f, 'Scenarios', data.SCENARIOS)
        pdat.param_dat(f, 'ScenarioLeafNode', ScenarioLeafNode, data.SCENARIOS)

        pdat.param_dat(f, 'StageCostVariable', StageCostVariable, stages)
        pdat.param_dat(f, 'ScenarioBasedData', False)

        f.write('set {} := \t{};\n'.format('StageVariables[FirstStage]',
                                           '\n\t\t'.join(FirstStageVariables)))

    # Defining the Second Stage differently as to allow for faster PH runs
    with open(fname('ScenarioStructureEF'), 'w') as f:
        f.write('set {} := {};\n\n'.format('StageVariables[SecondStage]',
                                           '\n\t'.join(SecondStageVariables)))

    with open(fname('ScenarioStructurePH'), 'w') as f:
        f.write('set {} := ;\n\n'.format('StageVariables[SecondStage]'))

    # Create reference files for check
    filenames = [fname('ScenarioStructureBase'), fname('ScenarioStructureEF')]
    cat_files(fname('ScenarioStructure'), filenames)

    # Create WW config file
    with open('config/wwph.suffixes', 'w') as f:
        FirstStageVariables = ['alpha_put', 'alpha_pick']
        Costs = [data.C_ALPHA, data.C_BETA]
        for idx, fsv in enumerate(FirstStageVariables):
            f.write('{}\t{}\t{}\n'.format(fsv, 'CostForRho', Costs[idx]))



    return os.path.isfile(fname('ScenarioStructure'))
