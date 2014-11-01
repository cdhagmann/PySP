import random
import csv
import itertools
from itertools import chain
from pdat import *
import sys
import os
import fileinput
import shutil
from query import *
from time import sleep
import pickle


def cat_files(name, file_names):
    """Concatenate files similar to the BASH command cat.\n\n
       cat file1 file2 > file3 <---> cat_files(file3,[file1,file2])"""
    with open(name, 'w') as f:
        for line in fileinput.input(file_names):
            f.write(line)


def add_dict(x, y):
    return dict(x, **y)


def bash_command(command, output=False):
    """Run BASH command in Python Script and return stdout as list.\n
       print '\n'.join(bash_command(command)) will properly display stdout to stdout"""
    import os

    stdin, stdout = os.popen2(command)
    stdin.close()
    lines = stdout.readlines()
    stdout.close()
    lines = [line.strip('\n') for line in lines]

    if output:
        print '\n'.join(lines)

    return lines


def multiple_replace(string, rep_dict):
    import re

    pattern = re.compile("|".join([re.escape(k) for k in rep_dict.keys()]), re.M)
    return pattern.sub(lambda x: rep_dict[x.group(0)], string)


class Struct():
    pass


''' Generates instances for the WITP problem'''


def instance_generator(S, V, P, Q, T, AD=None, DEFAULT=True, seed=None):
    I, J = 6, 6
    hpt = 8  # hours per time period t
    tpy = 28  # time period per year

    if seed is None:
        seed = query('seed value: ', **q_opts(-1, float, DEFAULT))
        if seed < 0:
            seed = round(1000 * random.random(), 2)

    random.seed(seed)

    # -----------------------------------------------------------------------------
    # SET NUMBER OF EVERYTHING
    # -----------------------------------------------------------------------------

    rd = Struct()

    rd.STORES = list("s" + str(s + 1) for s in xrange(S))

    rd.PRODUCTS = list("p" + str(p + 1) for p in xrange(P))
    rd.FASHION = list("q" + str(q + 1) for q in xrange(Q))
    items = rd.PRODUCTS + rd.FASHION

    rd.PUTAWAY = list("i" + str(i + 1) for i in xrange(I))
    rd.PICKING = list("j" + str(j + 1) for j in xrange(J))
    tech = rd.PUTAWAY + rd.PICKING

    rd.TIMES = list("" + str(t + 1) for t in xrange(T))
    rd.TIMES = range(1, T + 1)
    rd.T_minus_One = dict(zip(rd.TIMES[1:] + rd.TIMES[0:-1], rd.TIMES))

    Vq = int(Q * V / (P + Q))
    Vp = V - Vq

    rd.VENDORS_Q = list("vq" + str(v + 1) for v in xrange(Vq))
    rd.VENDORS_P = list("vp" + str(v + 1) for v in xrange(Vp))
    rd.VENDORS = rd.VENDORS_P + rd.VENDORS_Q

    # -----------------------------------------------------------------------------
    # GENERATE MODEL PARAMETERS
    # -----------------------------------------------------------------------------

    # Generate fashion period window
    rd.L_s = {s: 0 for s in rd.STORES}
    maxL = max(rd.L_s.values())
    rd.pt = 1

    tb_range = range(1, T + 1)

    try:
        for i in xrange(8):
            tb_default = tb_range[-i]
    except:
        pass

    rd.tb = query('fashion period start: ',
                  **q_opts(tb_default, tb_range, int, DEFAULT, False))

    te_range = range(rd.tb, T - maxL - rd.pt + 1)
    rd.te = query('fashion period end: ',
                  **q_opts(te_range[-1], te_range, int, DEFAULT, False))

    rd.ty = rd.te + rd.pt + maxL

    P_ratio = P / Vp
    Q_ratio = Q / Vq

    Omega = {}

    v_to_p = []

    if P_ratio > 0:
        PRODUCTS = list(rd.PRODUCTS)
        for v in rd.VENDORS_P:
            p_from_v = [PRODUCTS.pop(0) for _ in xrange(P_ratio)]
            v_to_p += [(v, p) for p in p_from_v]
        else:
            v_to_p += [(v, p) for p in PRODUCTS]
    else:
        v_to_p += zip(rd.VENDORS_P, rd.PRODUCTS)

    if Q_ratio > 0:
        FASHION = list(rd.FASHION)
        for v in rd.VENDORS_Q:
            q_from_v = [FASHION.pop(0) for _ in xrange(Q_ratio)]
            v_to_p += [(v, q) for q in q_from_v]
        else:
            v_to_p += [(v, q) for q in FASHION]

    else:
        v_to_p += zip(rd.VENDORS_Q, rd.FASHION)

    vqq = list(itertools.product(rd.VENDORS_Q, rd.FASHION))
    vpp = list(itertools.product(rd.VENDORS_P, rd.PRODUCTS))
    Omega = {(v, p): 1 if (v, p) in v_to_p else 0 for v, p in chain(vqq, vpp)}

    rd.Omega_q = [(v, q) for v in rd.VENDORS_Q for q in rd.FASHION if Omega[v, q]]
    rd.Omega_p = [(v, p) for v in rd.VENDORS_P for p in rd.PRODUCTS if Omega[v, p]]

    #Generate labor costs for full- and part-time employers
    ft_hourly = query('full time labor costs: ', **q_opts(40, [25], int, DEFAULT))
    pt_hourly = 30 if ft_hourly == 40 else 20

    rd.C_alpha = ft_hourly * hpt * T
    rd.C_beta = pt_hourly * hpt


    # Generate various sensitivity parameters
    rd.gamma = query('gamma: ', **q_opts(.5, [.5, 1, 1.5, 2], float, DEFAULT))
    rd.phi_put = query('phi_1: ', **q_opts(1, [.75, 1], float, DEFAULT))
    rd.phi_pick = rd.phi_put

    # Generate volume of the truck
    rd.script_Q = 15000


    # Generate product characteristics (Volume and Weight)
    rd.V_p = {p: round(random.uniform(.01, 1.0), 2) for p in rd.PRODUCTS}
    rd.V_q = {q: round(random.uniform(.01, 1.0), 2) for q in rd.FASHION}
    rd.W_p = {p: round(random.uniform(0.1, .99), 2) for p in rd.PRODUCTS}
    rd.W_q = {q: round(random.uniform(0.1, .99), 2) for q in rd.FASHION}

    # Generate cost of various technologies

    putaway_tech_choices = [(600, 0),
                            (1200, 5945),
                            (2400, 19817),
                            (3600, 26849),
                            (4800, 57534),
                            (6000, 76712)]

    picking_tech_choices = [(100, 639),
                            (200, 3388),
                            (300, 7671),
                            (400, 11506),
                            (500, 17900),
                            (1000, 51141)]

    rd.MHE = dict(zip(rd.PUTAWAY, [9, 27, 37, 87, 0, 0]))

    temp = dict(zip(tech, putaway_tech_choices + picking_tech_choices))
    Ct = {t: int((temp[t][1] / tpy) * T) for t in tech}
    rd.C_put = {i: Ct[i] for i in rd.PUTAWAY}
    rd.C_pick = {j: Ct[j] for j in rd.PICKING}

    Lambda = {t: temp[t][0] * hpt for t in tech}
    rd.lambda_put = {i: Lambda[i] for i in rd.PUTAWAY}
    rd.lambda_pick = {j: Lambda[j] for j in rd.PICKING}

    spt = itertools.product(rd.STORES, rd.PRODUCTS, rd.TIMES)
    sq = itertools.product(rd.STORES, rd.FASHION)

    Base_Load = 4000. / (P + Q) if AD is None else AD
    random_load = Base_Load, .4 * Base_Load

    daily_load = lambda: int(max([0, round(random.normalvariate(*random_load), 0)]))

    rd.Demand = {(s, p, t): daily_load() for s, p, t in spt}

    rd.X_osq = {(s, q): daily_load() * T for s, q in sq}
    rd.X_ivq = {(v, q): sum([rd.X_osq[s, q] for s in rd.STORES]) * Omega[v, q] for v, q in vqq}

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

    '''Randomly generate distances'''
    dist_VW, dist_WS, Cf, Cv, Cvf = {}, {}, {}, {}, {}

    for v in rd.VENDORS:
        dist_VW[v] = random.choice([x for x in DistanceInMiles if x >= 250])
        Cf[v] = FixedCost[dist_VW[v]]
        Cv[v] = Variable[dist_VW[v]]
        Cvf[v] = Variable_Fixed[dist_VW[v]]

    for s in rd.STORES:
        rnd_num = random.random()
        if rnd_num <= .4:
            dist_WS[s] = random.choice([x for x in DistanceInMiles if x <= 300])
        elif .4 < rnd_num <= .7:
            dist_WS[s] = random.choice([x for x in DistanceInMiles if 300 <= x <= 800])
        else:
            dist_WS[s] = random.choice(DistanceInMiles)

        Cf[s] = FixedCost[dist_WS[s]]
        Cv[s] = Variable[dist_WS[s]]
        Cvf[s] = Variable_Fixed[dist_WS[s]]

    rd.C_vs = {s: Cv[s] for s in rd.STORES}
    rd.C_fv = {v: Cvf[v] + Cf[v] for v in rd.VENDORS}
    rd.C_fs = {s: Cvf[s] + Cf[s] for s in rd.STORES}
    rd.C_vv = {v: Cv[v] for v in rd.VENDORS}


    #-------------------------------------------------------------------
    #                  CREATE BHANU'S HEURISTIC FILES 
    #-------------------------------------------------------------------

    warehouses = ['w1']

    WarehouseVolume = {w: 100000000 for w in warehouses}
    K = {s: 10000000 for s in rd.STORES}

    key = 'v{}q{}s{}p{}t{}'.format(V, Q, S, P, T)
    filename = 'WITPdataSet_' + key + '.txt'
    with open(filename, 'wb') as g:
        Xpress_data(g, 'WarehouseVolume', WarehouseVolume, warehouses)
        Xpress_data(g, 'StoreVolume', K, rd.STORES)
        Xpress_data(g, 'StoreDemand', rd.Demand, [rd.STORES, rd.PRODUCTS, rd.TIMES])
        Xpress_data(g, 'FixedCostVendorToWarehouse', Cf, [rd.VENDORS_P, warehouses])
        Xpress_data(g, 'FixedCostWarehouseToStore', Cf, [warehouses, rd.STORES])
        Xpress_data(g, 'Variable_FixedCostVendorToWarehouse', Cvf, [rd.VENDORS_P, warehouses])
        Xpress_data(g, 'VariableCostVendorToWarehouse', Cv, [rd.VENDORS_P, warehouses])
        Xpress_data(g, 'Variable_FixedCostWarehouseToStore', Cvf, [warehouses, rd.STORES])
        Xpress_data(g, 'VariableCostWarehouseToStore', Cv, [warehouses, rd.STORES])
        Xpress_data(g, 'ProductVolume', rd.V_p, rd.PRODUCTS)
        Xpress_data(g, 'ProductWeight', rd.W_p, rd.PRODUCTS)
        Xpress_data(g, 'MapVendorToProduct', Omega, [rd.VENDORS_P, rd.PRODUCTS])
        Xpress_data(g, 'LeadTimeWarehouseToStores', rd.L_s, [warehouses, rd.STORES])
        Xpress_data(g, 'StoreDemandForFashionProducts', rd.X_osq, [rd.STORES, rd.FASHION])
        Xpress_data(g, 'FixedCostFashionVendorToWarehouse', Cf, [rd.VENDORS_Q, warehouses])
        Xpress_data(g, 'Variable_FixedCostFashionVendorToWarehouse', Cvf, [rd.VENDORS_Q, warehouses])
        Xpress_data(g, 'VariableCostFashionVendorToWarehouse', Cv, [rd.VENDORS_Q, warehouses])
        Xpress_data(g, 'FashionProductVolume', rd.V_q, rd.FASHION)
        Xpress_data(g, 'FashionProductWeight', rd.W_q, rd.FASHION)
        Xpress_data(g, 'MapFashionVendorToProduct', Omega, [rd.VENDORS_Q, rd.FASHION])

    print "Created {FILE}".format(FILE=filename)

    SED = {}

    SED['FILENAMEVAL'] = key
    SED['FULLTIMECOSTVAL'] = rd.C_alpha / T
    SED['PARTTIMECOSTVAL'] = rd.C_beta
    SED['GAMMAVAL'] = rd.gamma
    SED['PHIVAL'] = rd.phi_put
    SED['BEGINTIMEVAL'] = rd.tb - 1
    SED['ENDTIMEVAL'] = rd.te - 1
    SED['DUETIMEVAL'] = rd.ty - 1
    SED['PROCESSINGTIMEVAL'] = rd.pt

    LARGE_FILE = sum(1 for _ in open(filename)) > 100000

    SED['NOTOTALITERATIONSVAL'] = 200 if LARGE_FILE else 1000
    SED['NOOFITERATIONSVAL'] = 200 if LARGE_FILE else 1000
    SED['NUMSWAPITERATIONSVAL'] = 3 if LARGE_FILE else 5
    SED['STOPITERVAL'] = 3 if LARGE_FILE else 5

    SED = {k: str(v) for k, v in SED.items()}

    with open('BhanuCode/WITP-TPH/TEMPLATE.cs', 'r') as f:
        lines = f.readlines()

    for i in range(100):
        lines[i] = multiple_replace(lines[i], SED)

    with open('BhanuCode/WITP-TPH/TPH.cs', 'w') as f:
        for line in lines:
            f.write(line)

    _ = bash_command('xbuild BhanuCode/WITP-TPH.sln')
    _ = bash_command('rm -f WITP-TPH.exe')
    _ = bash_command('cp BhanuCode/WITP-TPH/bin/Debug/WITP-TPH.exe ./')
    _ = bash_command('cp BhanuCode/WITP-TPH/TPH.cs ./')

    print "Compiled WITP-TPH.exe"

    #-------------------------------------------------------------------
    #                  CREATE PYOMO FILES 
    #-------------------------------------------------------------------       

    with open('PyomoCode/Pickled_Data', 'wb') as f:
        pickle.dump(rd, f, protocol=-1)

    print "Pickled Data"

    return rd if os.path.isfile('WITP-TPH.exe') else False


def main():
    DEFAULT = query('Use default values for Indices? ', default='y', response=boolean)
    S = query('Number of stores: ', **q_opts(3, int, DEFAULT))
    V = query('Number of vendors: ', **q_opts(3, int, DEFAULT))
    P = query('Number of basic products: ', **q_opts(3, int, DEFAULT))
    Q = query('Number of fashion products: ', **q_opts(3, int, DEFAULT))
    T = query('Number of time periods: ', **q_opts(7, int, DEFAULT))
    DEFAULT = query('Use default values for parameters? ', default='y', response=boolean)
    print
    rd = instance_generator(S, V, P, Q, T, DEFAULT=DEFAULT)
    if rd:
        print "Instance Created!"
    else:
        print "Failed to create instance!"
    return rd


if __name__ == '__main__':
    rd = main()	  
  
