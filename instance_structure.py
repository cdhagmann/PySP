# -*- coding: utf-8 -*-
"""
Created on Tue Nov  4 17:54:32 2014

@author: cdhagmann
"""

import random
import itertools
import pdat
import sys
import os
import fileinput
import shutil
import pickle
from Crispin.bash import id_generator

DISTANCE_IN_MILES = [25, 50, 75, 100, 150,
                     200, 250, 300, 350, 400,
                     500, 600, 700, 800, 900, 1000, 1100]

FIXED_COST = [40.42, 45.59, 52.27, 66.13, 75.28,
                   85.67, 97.5, 110.96, 126.26, 143.71,
                   186.09, 217.05, 253.17, 297.11, 344.43, 401.77, 468.61]

VARIABLE_FIX = [427.6, 441.14, 482.83, 492.45, 521.43,
                   541.39, 570.02, 598.03, 622.3, 659.96,
                   727.61, 802.19, 884.41, 975.07, 1075.01, 1185.2, 1306.68]

VARIABLE = [0.022, 0.027, 0.029, 0.034, 0.036,
                 0.041, 0.042, 0.045, 0.047, 0.05,
                 0.055, 0.061, 0.067, 0.074, 0.081, 0.09, 0.099]

def randomize(number, stdev=.1):
    """
    Returns a number from the normal distribution described with mean of
    number with standard deviation of stdev * number.
    """
    random_load = random.normalvariate(number, stdev * number)
    return int(max([0, round(random_load, 0)]))

def scale(lower_bound, upper_bound, number):
    """
    Create an evenly spaced list of specified number where
    returned_list[0] == lower_bound and returned_list[-1] == upper_bound
    """
    gen = (1. * n / (number - 1) for n in xrange(number))
    return [lower_bound + (upper_bound - lower_bound) * g for g in gen]


def cat_files(name, filenames):
    with open(name, 'w') as f:
        for line in fileinput.input(filenames):
            f.write(line)


class InstanceStructure():

    def __init__(self, S, V, P, I, J, T, K, seed=None):
        self.seed = round(1000 * random.random(), 2) if seed is None else seed

        self.STORES = ["s" + str(s + 1) for s in xrange(S)]
        self.VENDORS = ["v" + str(v + 1) for v in xrange(V)]
        self.PRODUCTS = ["p" + str(p + 1) for p in xrange(P)]
        self.PUTAWAY = ["i" + str(i + 1) for i in xrange(I)]
        self.PICKING = ["j" + str(j + 1) for j in xrange(J)]
        self.TIMES = [str(t + 1) for t in xrange(T)]
        self.SCENARIOS = ["k" + str(k + 1) for k in xrange(K)]

        self.case = '_'.join(['{}'] * 7).format(S, V, P, I, J, T, K)

        self.S, self.V, self.P, self.T = S, V, P, T
        self.I, self.J, self.K = I, J, K

        random.seed(self.seed)

        self.ID = id_generator()
        self.generate_fixed_data()
        self.generate_random_data()
        self.generate_technology_data()
        self.generate_demand_data()
        self.generate_transportation_data()
        self.write()

    @classmethod
    def from_file(cls, ID):
        archive = 'Instances/instance_{}.pickle'.format(ID)
        if os.path.isfile(archive):
            with open(archive, 'rb') as f:
                cls = pickle.load(f)
                return cls

    def write(self):
        archive = 'Instances/instance_{}.pickle'.format(self.ID)
        with open(archive, 'wb') as f:
            pickle.dump(self, f, protocol=-1)

    def generate_fixed_data(self):
        self.GAMMA = 1.0
        self.DELTA = 1.0
        self.ETA = 1.0
        self.SCRIPTQ = 15000
        self.AVERAGE_LOAD = min([4000. / self.P, 50])
        self.prob = {k: 1.0 / self.K for k in self.SCENARIOS}
        self.Cz_p, self.Cz_sp, self.Cr_p = {}, {}, {}
        for p in self.PRODUCTS:
            self.Cz_p[p] = .05
            self.Cr_p[p] = .10
            for s in self.STORES:
                self.Cz_sp[s, p] = .05

    def generate_random_data(self):
        FT_HOURLY = random.randint(25, 40)
        PT_HOURLY = random.randint(20, min([FT_HOURLY - 1, 30]))

        self.C_ALPHA = FT_HOURLY * 8.0 * self.T
        self.C_BETA = PT_HOURLY * 8.0

        self.VOLUME, self.WEIGHT = {}, {}
        for p in self.PRODUCTS:
            self.VOLUME[p] = round(random.random() * .1 + .01, 2)
            self.WEIGHT[p] = round(random.random() * .1 + .90, 2)

    def generate_technology_data(self):
        self.TECH_COST, self.LAMBDA = {}, {}

        RATE_SCALE = scale(4800, 48000, self.I)
        COST_SCALE = scale(0, .06, self.I)

        for i, t in enumerate(self.PUTAWAY):
            self.LAMBDA[t] = randomize(RATE_SCALE[i])
            self.TECH_COST[t] = randomize(self.LAMBDA[t] * COST_SCALE[i])

        RATE_SCALE = scale(800, 8000, self.J)
        COST_SCALE = scale(.03, .15, self.J)

        for i, t in enumerate(self.PICKING):
            self.LAMBDA[t] = randomize(RATE_SCALE[i])
            self.TECH_COST[t] = randomize(self.LAMBDA[t] * COST_SCALE[i])

        self.Lambda_put = {i: self.LAMBDA[i] for i in self.PUTAWAY}
        self.Lambda_pick = {j: self.LAMBDA[j] for j in self.PICKING}

        self.Cth_put = {i: self.TECH_COST[i] for i in self.PUTAWAY}
        self.Cth_pick = {j: self.TECH_COST[j] for j in self.PICKING}

    def generate_demand_data(self):
        self.DEMAND = {}
        for s in self.STORES:
            for p in self.PRODUCTS:
                mu = randomize(self.AVERAGE_LOAD, .4)
                for t in self.TIMES:
                    demands = [randomize(mu, .25) for _ in xrange(self.K)]
                    mu = random.choice(demands)
                    for k, d in zip(self.SCENARIOS, sorted(demands)):
                        self.DEMAND[s, p, t, k] = d

        self.BigM = 0
        for s in self.STORES:
            for p in self.PRODUCTS:
                for k in self.SCENARIOS:
                    temp = sum(self.DEMAND[s, p, t, k] for t in self.TIMES)
                    self.BigM = temp + 1 if temp > self.BigM else self.BigM

    def generate_transportation_data(self):
        self.Cv_v, self.Cf_v = {}, {}
        for v in self.VENDORS:
            dist_subset = [x for x in DISTANCE_IN_MILES if x >= 250]
            distance = random.choice(dist_subset)
            idx = DISTANCE_IN_MILES.index(distance)
            self.Cf_v[v] = FIXED_COST[idx] + VARIABLE_FIX[idx]
            self.Cv_v[v] = VARIABLE[idx]

        self.Cv_s, self.Cf_s = {}, {}
        for s in self.STORES:
            rnd_num = random.random()
            if rnd_num <= .4:
                dist_subset = [x for x in DISTANCE_IN_MILES if x <= 300]
            elif .4 < rnd_num <= .7:
                dist_subset = [x for x in DISTANCE_IN_MILES if 300 <= x <= 800]
            else:
                dist_subset = DISTANCE_IN_MILES

            distance = random.choice(dist_subset)
            idx = DISTANCE_IN_MILES.index(distance)
            self.Cf_s[s] = FIXED_COST[idx] + VARIABLE_FIX[idx]
            self.Cv_s[s] = VARIABLE[idx]

    def create_node_data(self, method=None):
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
            shutil.rmtree('models_{}/nodedata'.format(mthd))
            os.mkdir('models_{}/nodedata'.format(mthd))

            def mpath(archive):
                return 'models_{}/nodedata/{}.dat'.format(mthd, archive)

            with open(mpath('RootNodeBase'), 'w') as f:
                f.write('# Case of size [{}]\n\n'.format(self.case))

                pdat.set_dat(f, 'STORES', self.STORES)
                pdat.set_dat(f, 'PRODUCTS', self.PRODUCTS)
                pdat.set_dat(f, 'VENDORS', self.VENDORS)
                pdat.set_dat(f, 'TIMES', self.TIMES)
                if mthd in ('RLT', 'BigM'):
                    pdat.set_dat(f, 'PUTAWAY', self.PUTAWAY)
                    pdat.set_dat(f, 'PICKING', self.PICKING)

                if mthd == 'GBB':
                    IJ = list(itertools.product(self.PUTAWAY, self.PICKING))

                    for idx, (i, j) in enumerate(IJ):
                        file_name = 'Tech{}Node'.format(idx)
                        with open(mpath(file_name), 'w') as g:
                            pdat.param_dat(g, 'Lambda_put', self.Lambda_put[i])
                            pdat.param_dat(g, 'Lambda_pick', self.Lambda_pick[j])
                            pdat.param_dat(g, 'Cth_put', self.Cth_put[i])
                            pdat.param_dat(g, 'Cth_pick', self.Cth_pick[j])
                else:
                    pdat.param_dat(f, 'Lambda_put', self.Lambda_put, self.PUTAWAY)
                    pdat.param_dat(f, 'Lambda_pick', self.Lambda_pick, self.PICKING)
                    pdat.param_dat(f, 'Cth_put', self.Cth_put, self.PUTAWAY)
                    pdat.param_dat(f, 'Cth_pick', self.Cth_pick, self.PICKING)

                pdat.param_dat(f, 'A_put', self.AVERAGE_LOAD)
                pdat.param_dat(f, 'A_pick', self.AVERAGE_LOAD)

                pdat.param_dat(f, 'gamma', self.GAMMA)
                pdat.param_dat(f, 'delta', self.DELTA)

                pdat.param_dat(f, 'eta_put', self.ETA)
                pdat.param_dat(f, 'eta_pick', self.ETA)

                pdat.param_dat(f, 'ScriptQ', self.SCRIPTQ)
                pdat.param_dat(f, 'V_p', self.VOLUME, self.PRODUCTS)
                pdat.param_dat(f, 'W_p', self.WEIGHT, self.PRODUCTS)

                pdat.param_dat(f, 'Cf_v', self.Cf_v, self.VENDORS)
                pdat.param_dat(f, 'Cv_v', self.Cv_v, self.VENDORS)
                pdat.param_dat(f, 'Cf_s', self.Cf_s, self.STORES)
                pdat.param_dat(f, 'Cv_s', self.Cv_s, self.STORES)

                pdat.param_dat(f, 'Cz_p', self.Cz_p, self.PRODUCTS)
                pdat.param_dat(f, 'Cz_sp', self.Cz_sp, [self.STORES, self.PRODUCTS])

                pdat.param_dat(f, 'Cr_p', self.Cr_p, self.PRODUCTS)

                pdat.param_dat(f, 'Ca', self.C_ALPHA)
                pdat.param_dat(f, 'Cb', self.C_BETA)

                if mthd == 'GBB':
                    pass
                elif mthd == 'RLT':
                    pdat.param_dat(f, 'M_alpha', 200)
                    pdat.param_dat(f, 'M_beta', 200)
                else:
                    pdat.param_dat(f, 'BigM', self.BigM)

    def create_scenario_data(self, method=None):
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
            def mpath(archive):
                return 'models_{}/nodedata/{}.dat'.format(mthd, archive)

            for idx, k in enumerate(self.SCENARIOS):
                file_name = 'Scenario{}Node'.format(idx+1)
                with open(mpath(file_name), 'w') as f:
                    f.write('# Demand data for Scenario {}\n\n'.format(idx + 1))
                    f.write('param d_spt :=\n')
                    spt = itertools.product(self.STORES, self.PRODUCTS, self.TIMES)
                    for s, p, t in spt:
                        info = (' '.join([s, p, t]), self.DEMAND[s, p, t, k])
                        f.write('{} {}\n'.format(*info))
                    f.write(';\n\n')

            # Create reference files for checks
            if mthd == 'GBB':
                filenames = [mpath('RootNodeBase'), mpath('Tech0Node')]
                cat_files(mpath('RootNode'), filenames)
            else:
                cat_files(mpath('RootNode'), (mpath('RootNodeBase')))

            filenames = [mpath('RootNode'), mpath('Scenario1Node')]
            cat_files(mpath('ReferenceModel'), filenames)

            # Create the base of the ScenarioStructure file
            with open(mpath('ScenarioStructureBase'), 'w') as f:
                stages = ['FirstStage', 'SecondStage']

                scenarionodes = []
                p = {'RootNode': 1}
                NodeStage = {'RootNode': 'FirstStage'}
                for idx, k in enumerate(self.SCENARIOS, 1):
                    scenario_node = 'Scenario{}Node'.format(idx)
                    scenarionodes.append(scenario_node)
                    p[scenario_node] = self.prob[k]
                    NodeStage[scenario_node] = 'SecondStage'

                nodes = ['RootNode'] + scenarionodes
                StageCostVariable = {stage:'{}Cost'.format(stage) for stage in stages}

                ScenarioLeafNode = dict(zip(self.SCENARIOS, scenarionodes))


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
                                            'xi_pick[*,*]']

                pdat.set_dat(f, 'Stages', stages)
                pdat.set_dat(f, 'Nodes', nodes)

                pdat.param_dat(f, 'NodeStage', NodeStage, nodes)
                pdat.set_dat(f, 'Children[RootNode]', scenarionodes)
                pdat.param_dat(f, 'ConditionalProbability', p, nodes)
                pdat.set_dat(f, 'Scenarios', self.SCENARIOS)
                pdat.param_dat(f, 'ScenarioLeafNode', ScenarioLeafNode, self.SCENARIOS)

                pdat.param_dat(f, 'StageCostVariable', StageCostVariable, stages)
                pdat.param_dat(f, 'ScenarioBasedData', False)

                f.write('set {} := \t{};\n'.format('StageVariables[FirstStage]',
                                                   '\n\t\t'.join(FirstStageVariables)))

            # Defining the Second Stage differently as to allow for faster PH runs
            with open(mpath('ScenarioStructureEF'), 'w') as f:
                f.write('set {} := {};\n\n'.format('StageVariables[SecondStage]',
                                                   '\n\t'.join(SecondStageVariables)))

            with open(mpath('ScenarioStructurePH'), 'w') as f:
                f.write('set {} := ;\n\n'.format('StageVariables[SecondStage]'))

            # Create reference files for check
            filenames = [mpath('ScenarioStructureBase'), mpath('ScenarioStructureEF')]
            cat_files(mpath('ScenarioStructure'), filenames)

            # Create WW config file
            with open('config/wwph.suffixes', 'w') as f:
                FirstStageVariables = ['alpha_put', 'alpha_pick']
                Costs = [self.C_ALPHA, self.C_BETA]
                for idx, fsv in enumerate(FirstStageVariables):
                    f.write('{} {} {}\n'.format(fsv, 'CostForRho', Costs[idx]))
