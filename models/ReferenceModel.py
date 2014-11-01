#-----------------------------------------------------------------------------
#                              IMPORT MODULES
#-----------------------------------------------------------------------------

from coopr.pyomo import *

import itertools
from itertools import product, chain

#-----------------------------------------------------------------------------
#                            MOTIVATION FROM WIFE
#-----------------------------------------------------------------------------

''' my husband is amazingly sexy! RAWR!! love, sara '''


#-----------------------------------------------------------------------------
#                          DEFINE TUPLE FUNCTIONS
#-----------------------------------------------------------------------------


def flatten(x):
    result = []
    for item in x:
        if hasattr(item, "__iter__") and not isinstance(item, basestring):
            result.extend(flatten(item))
        else:
            result.append(item)
    return tuple(result)


def tup_list(*args):
    if len(args) == 1:
        return tuple(*args)
    else:
        return tuple(itertools.imap(flatten, product(*args)))

def print_dict(d):
    col = {1: 30, 2: 12}
    cspace = (lambda c, itm: str(itm) + (' ' * (col[c] - len(str(itm)))))
    keys = tuplelist([k for k in d])
    keys = sorted(keys, key=lambda tup: int(tup_str(tup)))
    for k in keys:
        v = d[k]
        if hasattr(v, 'X'):
            v = v.X
        elif hasattr(v, 'varName'):
            v = v.varName
        print cspace(1, k), cspace(2, v)

#-----------------------------------------------------------------------------
#                               INITIATE MODEL
#-----------------------------------------------------------------------------

model = AbstractModel()

#-----------------------------------------------------------------------------
#                           DECLARE MODEL PARAMETERS
#-----------------------------------------------------------------------------

# Model Indices

model.STORES = Set()
model.PRODUCTS = Set()
model.VENDORS = Set()
model.PUTAWAY = Set()
model.PICKING = Set()
model.TIMES = Set()



model.T_minus_One = Param(model.TIMES)
# Average Workload in the putaway (picking) area at the warehouse
model.PutawayAverageWorkload = Param(within=PositiveReals)
model.PickingAverageWorkload = Param(within=PositiveReals)
# Fraction of average warehouse workload to be assigned to full-time workers (gamma)
model.FractionalFullTimeLoad = Param(within=PositiveReals)
# Max ratio of part-time workers to full-time worker (delta)
model.MaxWorkerRatio = Param(within=PositiveReals)
# Ratio of part-time to full-time worker productivity for putaway (picking) (eta)
model.PutawayProductivityRatio = Param(within=PositiveReals)
model.PickingProductivityRatio = Param(within=PositiveReals)
# Generate volume of the truck
model.TruckVolume = Param(within=PositiveReals)
# Generate product characteristics (Volume and Weight)
model.ProductVolume = Param(model.PRODUCTS, within=PositiveReals)
model.ProductWeight = Param(model.PRODUCTS, within=PositiveReals)
# Fixed and variable transportation costs
model.VendorFixedTransportCost = Param(model.VENDORS, within=PositiveReals)
model.VendorVariableTransportCost = Param(model.VENDORS, within=PositiveReals)
model.StoreFixedTransportCost = Param(model.STORES, within=PositiveReals)
model.StoreVariableTransportCost = Param(model.STORES, within=PositiveReals)
# Holding cost for product p at the warehouse
model.ProductHoldingCostWarhouse = Param(model.PRODUCTS, within=PositiveReals)
model.ProductHoldingCostStore = Param(model.STORES, model.PRODUCTS, within=PositiveReals)
# Backlog cost for product p at store s
model.ProductBacklogCost = Param(model.PRODUCTS, within=PositiveReals)
# Labor costs for full- and part-time employers
model.FullTimeLaborCost = Param(within=PositiveReals)
model.PartTimeLaborCost = Param(within=PositiveReals)
# ProductDemand
model.Demand = Param(model.STORES, model.PRODUCTS, model.TIMES, within=NonNegativeIntegers)
# A Large Number
model.M = Param(within=NonNegativeIntegers)



# Average putaway (picking) rate per worker (Lambda)
model.PutawayRate = Param(within=PositiveReals)
model.PickingRate = Param(within=PositiveReals)
# Deployment cost of various technologies
model.PutawayTechCost = Param(within=PositiveReals)
model.PickingTechCost = Param(within=PositiveReals)

#-----------------------------------------------------------------------------
#                           DECLARE MODEL VARIABLES
#-----------------------------------------------------------------------------

model.FirstStageCost = Var()
model.SecondStageCost = Var()


# alpha
model.PutawayFullTimeWorkers = Var(bounds=(0.0, model.M), within=NonNegativeIntegers)
model.PickingFullTimeWorkers = Var(bounds=(0.0, model.M), within=NonNegativeIntegers)

# beta
model.PutawayPartTimeWorkers = Var(model.TIMES, bounds=(0.0, model.M), within=NonNegativeIntegers)
model.PickingPartTimeWorkers = Var(model.TIMES, bounds=(0.0, model.M), within=NonNegativeIntegers)

# n
model.ShipmentsWarehouse = Var(model.VENDORS, model.TIMES,
                               bounds=(0.0, None), within=NonNegativeIntegers)
model.ShipmentsToStore = Var(model.STORES, model.TIMES,
                             bounds=(0.0, None), within=NonNegativeIntegers)

# x
model.ProductInboundWarehouse = Var(model.VENDORS, model.PRODUCTS, model.TIMES,
                                    bounds=(0.0, None), within=NonNegativeIntegers)

# y
model.ProductOutboundWarehouse = Var(model.STORES, model.PRODUCTS, model.TIMES,
                                    bounds=(0.0, None), within=NonNegativeIntegers)

# z
model.ProductInventoryWarehouse = Var(model.PRODUCTS, model.TIMES,
                                    bounds=(0.0, None), within=NonNegativeIntegers)
model.ProductInventoryStore = Var(model.STORES, model.PRODUCTS, model.TIMES,
                                    bounds=(0.0, None), within=NonNegativeIntegers)

# r
model.ProductBacklogStore = Var(model.STORES, model.PRODUCTS, model.TIMES,
                                    bounds=(0.0, None), within=NonNegativeIntegers)

#-----------------------------------------------------------------------------
#                           DECLARE MODEL CONSTRAINTS
#-----------------------------------------------------------------------------


# First Stage Objective
def ComputeFirstStageCost_rule(model):
    FS_expr = model.FullTimeLaborCost * (model.PutawayFullTimeWorkers + model.PickingFullTimeWorkers)
    FS_expr += model.PutawayTechCost + model.PickingTechCost
    return (model.FirstStageCost - FS_expr) == 0.0

model.ComputeFirstStageCost = Constraint()


# Constraint 4
def ConstrainPutawayAverage_rule(model):
    return (model.PutawayAverageWorkload * model.FractionalFullTimeLoad <=
            model.PutawayFullTimeWorkers * model.PutawayRate)

model.ConstrainPutawayAverage = Constraint()


def ConstrainPickingAverage_rule(model):
    return (model.PickingAverageWorkload * model.FractionalFullTimeLoad <=
            model.PickingFullTimeWorkers * model.PickingRate)

model.ConstrainPickingAverage = Constraint()


###############################################################################

SP = [(s,p) for s in model.STORES for p in model.PRODUCTS]
VP = [(v,p) for v in model.VENDORS for p in model.PRODUCTS]

ST = [(s,t) for s in model.STORES for t in model.TIMES]
PT = [(p,t) for p in model.PRODUCTS for t in model.TIMES]
VT = [(v,t) for v in model.VENDORS for t in model.TIMES]

VPT = [(v,p,t) for v in model.VENDORS for p in model.PRODUCTS for t in model.TIMES]
SPT = [(s,p,t) for s in model.STORES for p in model.PRODUCTS for t in model.TIMES]



# Second Stage Objective
def ComputeSecondStageCost_rule(model):
    SS_expr1 = model.PartTimeLaborCost * sum((model.PutawayPartTimeWorkers[t] + model.PickingPartTimeWorkers[t])
                                            for t in model.TIMES)
    SS_expr2 = sum(model.ProductHoldingCostWarhouse[p] * model.ProductInventoryWarehouse[p,t]
                        for p in model.PRODUCTS for t in model.TIMES)
    SS_expr3 = sum(model.ProductHoldingCostStore[s,p] * model.ProductInventoryStore[s,p,t] 
                        for s in model.STORES for p in model.PRODUCTS for t in model.TIMES)
    SS_expr4 = sum(model.ProductBacklogCost[p] * model.ProductBacklogStore[s,p,t]
                        for s in model.STORES for p in model.PRODUCTS for t in model.TIMES)
    SS_expr5 = sum(model.VendorFixedTransportCost[v] * model.ShipmentsWarehouse[v,t]
                        for v in model.VENDORS for t in model.TIMES)
    SS_expr6 = sum(model.StoreFixedTransportCost[s] * model.ShipmentsToStore[s,t]
                        for s in model.STORES for t in model.TIMES)
    SS_expr7 = sum(model.ProductVolume[p] * model.VendorVariableTransportCost[v] * model.ProductInboundWarehouse[v,p,t]
                        for v in model.VENDORS for p in model.PRODUCTS for t in model.TIMES)
    SS_expr8 = sum(model.ProductVolume[p] * model.StoreVariableTransportCost[s] * model.ProductOutboundWarehouse[s,p,t]
                        for s in model.STORES for p in model.PRODUCTS for t in model.TIMES)
    return (model.SecondStageCost - SS_expr1 - SS_expr2 - SS_expr3 - SS_expr4 - SS_expr5
             - SS_expr6 - SS_expr7 - SS_expr8 == 0.0)

model.ComputeSecondStageCost = Constraint()

# Constraint 8
def ConstraintEight_rule(model, t):
    C8_expr1 = sum(model.ProductInboundWarehouse[v,p,t] for v in model.VENDORS for p in model.PRODUCTS)
    C8_expr2 = model.PutawayRate * (model.PutawayFullTimeWorkers + 
                                    model.PutawayProductivityRatio * model.PutawayPartTimeWorkers[t])
    return (C8_expr1 - C8_expr2 <= 0)

model.ConstraintEight = Constraint(model.TIMES)

# Constraint 9
def ConstraintNine_rule(model, t):
    C9_expr1 = sum(model.ProductOutboundWarehouse[s,p,t] for s in model.STORES for p in model.PRODUCTS)
    C9_expr2 = model.PickingRate * (model.PickingFullTimeWorkers + 
                                    model.PickingProductivityRatio * model.PickingPartTimeWorkers[t])
    return (C9_expr1 - C9_expr2 <= 0)

model.ConstraintNine = Constraint(model.TIMES)

# Constraint 10
def ConstraintTenPutaway_rule(model, t):
    C10_expr1 = model.PutawayPartTimeWorkers[t]
    C10_expr2 = model.MaxWorkerRatio * model.PutawayFullTimeWorkers
    return (C10_expr1 - C10_expr2 <= 0)
model.ConstraintTenPutaway = Constraint(model.TIMES)

def ConstraintTenPicking_rule(model, t):
    C10_expr1 = model.PickingPartTimeWorkers[t]
    C10_expr2 = model.MaxWorkerRatio * model.PickingFullTimeWorkers
    return (C10_expr1 - C10_expr2 <= 0)
model.ConstraintTenPicking = Constraint(model.TIMES)

       
# Constraint 11
def ConstraintEleven_rule(model, p, t):
    C11_expr1 = sum(model.ProductInboundWarehouse[v, p, t] for v in model.VENDORS)
    C11_expr1 -= sum(model.ProductOutboundWarehouse[s, p, t] for s in model.STORES)
    C11_expr2 = model.ProductInventoryWarehouse[p,t] - model.ProductInventoryWarehouse[p,model.T_minus_One[t]]

    return (C11_expr1 - C11_expr2 == 0)
model.ConstraintEleven = Constraint(model.PRODUCTS, model.TIMES)


# Constraint 12
def ConstraintTwelve_rule(model,s,p,t):
    C12_expr1 = model.ProductOutboundWarehouse[s, p, t] - model.ProductBacklogStore[s,p,t]
    C12_expr1 -= model.Demand[s,p,t] - model.ProductBacklogStore[s,p,model.T_minus_One[t]]
    C12_expr2 = model.ProductInventoryStore[s,p,t] - model.ProductInventoryStore[s,p,model.T_minus_One[t]]

    return (C12_expr1 - C12_expr2 == 0)

model.ConstraintTwelve = Constraint(model.STORES, model.PRODUCTS, model.TIMES)


# Constraints 13
def ConstraintThirteen_rule(model, v, t):
    C13_expr1 = sum(model.ProductVolume[p] * model.ProductInboundWarehouse[v, p, t] 
                         for p in model.PRODUCTS)
    C13_expr2 = model.TruckVolume * model.ShipmentsWarehouse[v,t]                    
    return (C13_expr1 - C13_expr2 <= 0)
model.ConstraintThirteen = Constraint(model.VENDORS, model.TIMES)


# Constraints 14
def ConstraintFourteen_rule(model, s, t):
    C14_expr1 = sum(model.ProductVolume[p] * model.ProductOutboundWarehouse[s, p, t] 
                         for p in model.PRODUCTS)
    C14_expr2 = model.TruckVolume * model.ShipmentsToStore[s,t]                    
    return (C14_expr1 - C14_expr2 <= 0)
model.ConstraintFourteen = Constraint(model.STORES, model.TIMES)


def Total_Cost_Objective_rule(model):
    return model.FirstStageCost + model.SecondStageCost

model.Total_Cost_Objective = Objective(sense=minimize)





