import random
import csv
import itertools
from itertools import chain
import pdat
import sys
import os
import fileinput
import shutil

'''Concatenate files similiar to the BASH command cat.\n\n
   cat file1 file2 > file3 <---> cat_files(file3,[file1,file2])'''
def cat_files(name,filenames):
    with open(name, 'w') as f:
        for line in fileinput.input(filenames):
            f.write(line)

'''Read Transportaion Cost from file'''
def read_transportation_costs():
	DistanceInMiles = []
	FixedCost = {}
	intercept = {}
	slope = {}

	with open("TransportationCost.txt",'r') as f:
		reader=csv.reader(f,delimiter='\t')
		for c1,c2,c3,c4 in reader:
			dist = int(c1)
			DistanceInMiles.append(dist)
			FixedCost[dist] = float(c2)
			intercept[dist] = float(c3)
			slope[dist] = float(c4)
	return DistanceInMiles,FixedCost,intercept,slope


''' Generates instances for the WITP Stochastic problem'''
def instance_generator(S,V,P,I,J,T,K):
    
    hpt = 8 # hours per time period t
    
    #-----------------------------------------------------------------------------
    #                          SET NUMBER OF EVERYTHING
    #-----------------------------------------------------------------------------

    stores = ["s" + str(s + 1) for s in xrange(S)]
    vendors = ["v" + str(v + 1) for v in xrange(V)]
    products = ["p" + str(p + 1) for p in xrange(P)]
    putaway = ["i" + str(i + 1) for i in xrange(I)]
    picking = ["j" + str(j + 1) for j in xrange(J)]
    times = [str(t+1) for t in xrange(T)]
    scenarios = ["k" + str(k + 1) for k in xrange(K)]
    times0 = dict(zip(times,times[1:] + times[0:-1]))

    #-----------------------------------------------------------------------------
    #                        GENERATE MODEL PARAMETERS
    #-----------------------------------------------------------------------------

    # Generate labor costs for full- and part-time employers
    ft_hourly = random.randint(25, 40)
    pt_hourly = random.randint(20, min([ft_hourly - 1,30]))

    Ca = ft_hourly * hpt * T
    Cb = pt_hourly * hpt   
    
    
    # Generate various sensitivity parameters
    gamma = 1
    delta = 1.0
    eta1 = 1.0
    eta2 = 1.0

    # Generate volume of the truck
    Q = 15000

    # Generate workload parameters
    A1 = 3 * Q
    A2 = 2 * Q

    # Generate product characteristics (Volume and Weight)
    Vol = {p: round(random.random() * .1 + .01, 2) for p in products}
    W = {p: round(random.random() * .1 + .9, 2) for p in products}

    # Generate cost of various technologies
    temp1 = [random.randint(5000, 10000) for t in chain(putaway, picking)]
    temp1.sort()
    temp2, LB, UB = [], 200, 400
    for i in range(len(temp1)):
        temp2.append(random.randint(LB, UB))
        LB, UB = temp2[i], temp2[i] + 150
    temp = zip(temp1, temp2)
    random.shuffle(temp)
    Ct = {t: temp[idx][0] for idx, t in enumerate(chain(putaway, picking))}
    Lambda = {t: temp[idx][1] for idx, t in enumerate(chain(putaway, picking))}
    Lambda1 = {i: Lambda[i] for i in putaway}
    Lambda2 = {j: Lambda[j] for j in picking}
                
    # Generate demand parameter
    def demand(val, K):
        per = lambda i: 1 if i == (K/2) else .75 + (float(i) / (K - 1)) * .5
        temp = map(per, range(K))
        return map(lambda x: round(x * val), temp)
        
    d = {}    
    for s in stores:
        for p in products:
            dem = demand(random.randint(400, 1600),K)
            for t in times:
                mu = random.choice(dem)
                dem = demand(mu, K)
                for idx, k in enumerate(scenarios):
                    d[s, p, t, k] = int(dem[idx])  

    # Data for holding cost for product p at the warehouse
    Cz = {tup: 0.05 for tup in chain(products, itertools.product(stores, products))}

    # Data for backlog cost for product p at store s
    Cr = {p: .10 for p in products}

    #-------------------------------------------------------------------
    #                  GENERATE TRANSPORTATION COSTS
    #-------------------------------------------------------------------

    '''[DistanceInMiles],{FixedCost},{Variable},{Variable_Fixed}'''
    # Read data from file
    DistanceInMiles,FixedCost,Variable_Fixed,Variable = read_transportation_costs()

    dist_VW, dist_WS, Cf, Cv = {}, {}, {}, {}

    dist_subset = [x for x in DistanceInMiles if x >= 250]
    for v in vendors:
        dist_VW[v] = random.choice(dist_subset)
        Cf[v] = FixedCost[dist_VW[v]]
        Cv[v] = Variable[dist_VW[v]]

    for s in stores:
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
        
    #-------------------------------------------------------------------
    #               GENERATE PROBABILITIES IF NOT PROVIDED
    #-------------------------------------------------------------------
    try:
        prob = {k: prob.get(k, .0001) for k in scenarios}
        prob_sum = sum(prob[k] for k in scenarios)
    except NameError:
        prob = {k: 1.0 / K for k in scenarios}
        prob_sum = sum(prob[k] for k in scenarios)
    finally:
        prob = {k: prob[k] * 1.0 / prob_sum for k in scenarios}
        prob_sum = sum(prob[k] for k in scenarios)
        
    #-------------------------------------------------------------------
    #                  CREATE NODEDATA FILES 
    #-------------------------------------------------------------------
    
    # Removes past files and starts over
    shutil.rmtree('nodedata')
    os.mkdir('nodedata')
    fname = lambda f: 'nodedata/{}.dat'.format(f)
    
    f = open(fname('RootNodeBase'), 'w')
    f.write('# Case of size [{},{},{},{},{},{},{}]\n\n'.format(S,V,P,I,J,T,K))

    pdat.set_dat(f,'STORES',stores)
    pdat.set_dat(f,'VENDORS',vendors)
    pdat.set_dat(f,'PRODUCTS',products)
    pdat.set_dat(f,'TIMES',times)


    pdat.param_dat(f,'T_minus_One', times0,times)
    pdat.param_dat(f,'PutawayAverageWorkload', A1)
    pdat.param_dat(f,'PickingAverageWorkload', A2)
    # Fraction of average warehouse workload to be assigned to full-time workers (gamma)
    pdat.param_dat(f,'FractionalFullTimeLoad', gamma)
    # Max ratio of part-time workers to full-time worker (delta)
    pdat.param_dat(f,'MaxWorkerRatio', delta)
    # Ratio of part-time to full-time worker productivity for putaway (picking) (eta)
    pdat.param_dat(f,'PutawayProductivityRatio', eta1)
    pdat.param_dat(f,'PickingProductivityRatio', eta2)
    # Generate volume of the truck
    pdat.param_dat(f,'TruckVolume', Q)
    # Generate product characteristics (Volume and Weight)
    pdat.param_dat(f,'ProductVolume', Vol, products)
    pdat.param_dat(f,'ProductWeight', W, products)
    # Fixed and variable transportation costs
    pdat.param_dat(f,'VendorFixedTransportCost', Cf, vendors)
    pdat.param_dat(f,'VendorVariableTransportCost', Cv, vendors)
    pdat.param_dat(f,'StoreFixedTransportCost', Cf, stores)
    pdat.param_dat(f,'StoreVariableTransportCost', Cv, stores)
    # Holding cost for product p at the warehouse
    pdat.param_dat(f,'ProductHoldingCostWarhouse', Cz, products)
    pdat.param_dat(f,'ProductHoldingCostStore', Cz, [stores, products])
    # Backlog cost for product p at store s
    pdat.param_dat(f,'ProductBacklogCost', Cr, products)
    # Labor costs for full- and part-time employers
    pdat.param_dat(f,'FullTimeLaborCost', Ca)
    pdat.param_dat(f,'PartTimeLaborCost', Cb)
    
    pdat.param_dat(f,'M', 1000)
    
    f.close()
    
    
    # Make educated guesses on which will be the optimal option for future work
    merit = lambda i: Ct[i]/float(Lambda[i])
    temp = list(itertools.product(putaway,picking))
    IJ = sorted(temp, key=lambda (i,j): merit(i) + merit(j))
    
    
    # Create the I x J Tech parameters files sinces namespaces doesn't work in PySP
    for idx,(i,j) in enumerate(IJ):
        file_name = 'Tech{}Node'.format(idx)
        f = open(fname(file_name), 'w')
        pdat.param_dat(f,'PutawayRate', Lambda1[i])
        pdat.param_dat(f,'PickingRate', Lambda2[j])
        pdat.param_dat(f,'PutawayTechCost', Ct[i])
        pdat.param_dat(f,'PickingTechCost', Ct[j])    
        f.close()
    
    
    # Create the scenario node files    
    for idx,k in enumerate(scenarios):
        file_name = 'Scenario{}Node'.format(idx+1)	
        f = open(fname(file_name), 'w')
        
        f.write('# Demand data for Scenario {}\n\n'.format(idx+1))
        f.write('param Demand :=\n')      
        for s,p,t in itertools.product(stores,products,times):
            f.write('{} {}\n'.format(' '.join([s,p,t]), d[s,p,t,k]))
        f.write(';\n\n')

        f.close()
    
    
    # Creat reference files for checks
    filenames = [fname('RootNodeBase'),fname('Tech0Node')]
    cat_files(fname('RootNode'),filenames)
    
    filenames = [fname('RootNode'),fname('Scenario1Node')]
    cat_files(fname('ReferenceModel'),filenames)
     
    # Create the base of the ScenarioStructure file            
    with open(fname('ScenarioStructureBase'), 'w') as f:         
        stages = ['FirstStage','SecondStage']
        scenarionodes = ['Scenario{}Node'.format(idx+1) for idx in range(len(scenarios))]
        nodes = ['RootNode'] + scenarionodes
         
        NodeStage = {NS:'SecondStage' for NS in scenarionodes}
        NodeStage['RootNode'] = 'FirstStage' 
        
        p = {'Scenario{}Node'.format(idx+1):prob[k] for idx,k in enumerate(scenarios)}
        p['RootNode'] = 1              
        StageCostVariable = {stage:'{}Cost'.format(stage) for stage in stages}
        
        ScenarioLeafNode = dict(zip(scenarios,scenarionodes))
        
        FirstStageVariables = ['PutawayFullTimeWorkers','PickingFullTimeWorkers']
        SecondStageVariables = ['PutawayPartTimeWorkers[*]', 'PickingPartTimeWorkers[*]',
                                'ShipmentsWarehouse[*,*]','ShipmentsToStore[*,*]',
                                'ProductInboundWarehouse[*,*,*]','ProductOutboundWarehouse[*,*,*]',
                                'ProductInventoryWarehouse[*,*]','ProductInventoryStore[*,*,*]',
                                'ProductBacklogStore[*,*,*]']      
                
        pdat.set_dat(f,'Stages',stages)
        pdat.set_dat(f,'Nodes',nodes)
        
        pdat.param_dat(f,'NodeStage',NodeStage,nodes)
        pdat.set_dat(f,'Children[RootNode]',scenarionodes)
        pdat.param_dat(f,'ConditionalProbability',p,nodes)
        pdat.set_dat(f,'Scenarios',scenarios)
        pdat.param_dat(f,'ScenarioLeafNode',ScenarioLeafNode,scenarios)
        
        pdat.param_dat(f,'StageCostVariable',StageCostVariable,stages)
        pdat.param_dat(f,'ScenarioBasedData',False)
        
        f.write('set {} := \t{};\n'.format('StageVariables[FirstStage]',
                                           '\n\t\t\t\t\t\t\t\t\t'.join(FirstStageVariables)))
    
    # Defining the Second Stage differently as to allow for faster PH runs                                       
    with open(fname('ScenarioStructureEF'), 'w') as f:                                           
        f.write('set {} := {};\n\n'.format('StageVariables[SecondStage]',
                                           '\n\t\t\t\t\t\t\t\t\t'.join(SecondStageVariables)))
    
    with open(fname('ScenarioStructurePH'), 'w') as f:                                           
        f.write('set {} := ;\n\n'.format('StageVariables[SecondStage]'))
    
    # Create reference files for check    
    filenames = [fname('ScenarioStructureBase'),fname('ScenarioStructureEF')]
    cat_files(fname('ScenarioStructure'),filenames)    
    
    # Create WW config file
    with open('config/wwph.suffixes', 'w') as f:
        FirstStageVariables = ['PutawayFullTimeWorkers','PickingFullTimeWorkers']
        Costs = [Ca,Cb]
        for idx,fsv in enumerate(FirstStageVariables):
            f.write('{}\t{}\t{}\n'.format(fsv,'CostForRho',Costs[idx]) ) 
    
        
            
    return os.path.isfile('nodedata/ScenarioStructure.dat')
	

'''Start of actually program'''	
if __name__ == '__main__':
    try:
        sys.argv[1]
        S = int(raw_input("Number of stores: "))
        V = int(raw_input("Number of vendors: "))
        P = int(raw_input("Number of products: "))
        I = int(raw_input("Number of putaway techs: "))
        J = int(raw_input("Number of picking techs: "))
        T = int(raw_input("Number of time periods: "))
        K = int(raw_input("Number of scenarios: "))
        print
        if instance_generator(S,V,P,I,J,T,K):
            print "Instance Generated!"
        else:
            print "Instance Failed!"	  
    except:
        if instance_generator(50,50,50,10,10,5,10):
	        print "Instance Generated!"
        else:
	        print "Instance Failed!"
  
