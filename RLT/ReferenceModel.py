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

M = AbstractModel()

#-----------------------------------------------------------------------------
#                           DECLARE MODEL PARAMETERS
#-----------------------------------------------------------------------------

# Model Indices

M.STORES = Set()
M.PRODUCTS = Set()
M.VENDORS = Set()
M.PUTAWAY = Set()
M.PICKING = Set()
M.TIMES = Set()
M.PICKING = Set()
M.PUTAWAY = Set()


M.T_minus_One = Param(M.TIMES)

M.Lambda_put = Param(M.PUTAWAY, within=PositiveReals)
M.Lambda_pick = Param(M.PICKING, within=PositiveReals)
M.A_put = Param(within=PositiveReals)
M.A_pick = Param(within=PositiveReals)
M.gamma = Param(within=PositiveReals)
M.delta = Param(within=PositiveReals)
M.eta_put = Param(within=PositiveReals)
M.eta_pick = Param(within=PositiveReals)
M.ScriptQ = Param(within=PositiveReals)
M.V_p = Param(M.PRODUCTS, within=PositiveReals)
M.W_p = Param(M.PRODUCTS, within=PositiveReals)
M.Cf_v = Param(M.VENDORS, within=PositiveReals)
M.Cf_s = Param(M.STORES, within=PositiveReals)
M.Cv_v = Param(M.VENDORS, within=PositiveReals)
M.Cv_s = Param(M.STORES, within=PositiveReals)
M.Cz_p = Param(M.PRODUCTS, within=PositiveReals)
M.Cz_sp = Param(M.STORES, M.PRODUCTS, within=PositiveReals)
M.Cth_put = Param(M.PUTAWAY, within=PositiveReals)
M.Cth_pick = Param(M.PICKING, within=PositiveReals)
M.C_rp = Param(M.PRODUCTS, within=PositiveReals)
M.Ca = Param(within=PositiveReals)
M.Cb = Param(within=PositiveReals)
M.d_spt = Param(M.STORES, M.PRODUCTS, M.TIMES, within=NonNegativeIntegers)

M.BigM = Param(within=NonNegativeIntegers, initialize=50)


#-----------------------------------------------------------------------------
#                           DECLARE MODEL VARIABLES
#-----------------------------------------------------------------------------

M.FirstStageCost = Var()
M.SecondStageCost = Var()

M.alpha_put = Var(bounds=(0.0, M.BigM), within=NonNegativeIntegers)
M.alpha_pick = Var(bounds=(0.0, M.BigM), within=NonNegativeIntegers)
M.theta_put = Var(M.PUTAWAY, within=Binary)
M.theta_pick = Var(M.PICKING, within=Binary)
M.lambda_put = Var(M.PUTAWAY, within=PositiveReals)
M.lambda_pick = Var(M.PICKING, within=PositiveReals)
M.beta_put = Var(M.TIMES, bounds=(0.0, M.BigM), within=NonNegativeIntegers)
M.beta_pick = Var(M.TIMES, bounds=(0.0, M.BigM), within=NonNegativeIntegers)
M.n_vt = Var(M.VENDORS, M.TIMES, within=NonNegativeIntegers)
M.n_st = Var(M.STORES, M.TIMES, within=NonNegativeIntegers)
M.x_vpt = Var(M.VENDORS, M.PRODUCTS, M.TIMES, within=NonNegativeIntegers)
M.y_spt = Var(M.STORES, M.PRODUCTS, M.TIMES,within=NonNegativeIntegers)
M.z_pt = Var(M.PRODUCTS, M.TIMES, within=NonNegativeIntegers)
M.z_spt = Var(M.STORES, M.PRODUCTS, M.TIMES, within=NonNegativeIntegers)
M.r_spt = Var(M.STORES, M.PRODUCTS, M.TIMES, within=NonNegativeIntegers)


# DUMMY VARIABLES

M.zeta_put = Var(M.PUTAWAY, bounds=(0.0, M.BigM), within=NonNegativeIntegers)
M.zeta_pick = Var(M.PICKING, bounds=(0.0, M.BigM), within=NonNegativeIntegers)

#-----------------------------------------------------------------------------
#                           DECLARE MODEL CONSTRAINTS
#-----------------------------------------------------------------------------


# First Stage Objective
def ComputeFirstStageCost_rule(M):
    FS_expr = M.Ca * (M.alpha_put + M.alpha_pick)
    FS_expr += summation(M.Cth_put, M.theta_put)
    FS_expr += summation(M.Cth_pick, M.theta_pick)
    return (M.FirstStageCost - FS_expr) == 0.0

M.ComputeFirstStageCost = Constraint()

# Constraint 2
def ConstraintPutawaySelection(M):
    return summation(M.theta_put) == 1
M.ConstraintPutawaySelection = Constraint()    
    
def ConstraintPickingSelection(M):
    return summation(M.theta_pick) == 1
M.ConstraintPickingSelection = Constraint()    

    
# Constraint 4
def ConstraintPutawayAverage_rule(M, i):
    return (M.A_put * M.gamma <= M.zeta_put[i] * M.Lambda_put[i])

M.ConstraintPutawayAverage = Constraint(M.PUTAWAY)


def ConstraintPickingAverage_rule(M, j):
    return (M.A_pick * M.gamma <=
            M.zeta_pick[j] * M.Lambda_pick[j])

M.ConstraintPickingAverage = Constraint(M.PICKING)


###############################################################################

# Second Stage Objective
def ComputeSecondStageCost_rule(M):
    SS_expr1 = M.Cb * sum((M.beta_put[t] + M.beta_pick[t])
                                            for t in M.TIMES)
    SS_expr2 = sum(M.Cz_p[p] * M.z_pt[p,t]
                        for p in M.PRODUCTS for t in M.TIMES)
    SS_expr3 = sum(M.Cz_sp[s,p] * M.z_spt[s,p,t] 
                        for s in M.STORES for p in M.PRODUCTS for t in M.TIMES)
    SS_expr4 = sum(M.C_rp[p] * M.r_spt[s,p,t]
                        for s in M.STORES for p in M.PRODUCTS for t in M.TIMES)
    SS_expr5 = sum(M.Cf_v[v] * M.n_vt[v,t]
                        for v in M.VENDORS for t in M.TIMES)
    SS_expr6 = sum(M.Cf_s[s] * M.n_st[s,t]
                        for s in M.STORES for t in M.TIMES)
    SS_expr7 = sum(M.V_p[p] * M.Cv_v[v] * M.x_vpt[v,p,t]
                        for v in M.VENDORS for p in M.PRODUCTS for t in M.TIMES)
    SS_expr8 = sum(M.V_p[p] * M.Cv_s[s] * M.y_spt[s,p,t]
                        for s in M.STORES for p in M.PRODUCTS for t in M.TIMES)
    return (M.SecondStageCost - SS_expr1 - SS_expr2 - SS_expr3 - SS_expr4 - SS_expr5
             - SS_expr6 - SS_expr7 - SS_expr8 == 0.0)

M.ComputeSecondStageCost = Constraint()

# Constraint 8
def ConstraintEight_rule(M, t):
    C8_expr1 = sum(M.x_vpt[v,p,t] for v in M.VENDORS for p in M.PRODUCTS)
    C8_expr2 = M.Lambda_put * (M.alpha_put + 
                                    M.eta_put * M.beta_put[t])
    return (C8_expr1 - C8_expr2 <= 0)

M.ConstraintEight = Constraint(M.TIMES)

# Constraint 9
def ConstraintNine_rule(M, t):
    C9_expr1 = sum(M.y_spt[s,p,t] for s in M.STORES for p in M.PRODUCTS)
    C9_expr2 = M.Lambda_pick * (M.alpha_pick + 
                                    M.eta_pick * M.beta_pick[t])
    return (C9_expr1 - C9_expr2 <= 0)

M.ConstraintNine = Constraint(M.TIMES)

# Constraint 10
def ConstraintTenPutaway_rule(M, t):
    C10_expr1 = M.beta_put[t]
    C10_expr2 = M.delta * M.alpha_put
    return (C10_expr1 - C10_expr2 <= 0)
M.ConstraintTenPutaway = Constraint(M.TIMES)

def ConstraintTenPicking_rule(M, t):
    C10_expr1 = M.beta_pick[t]
    C10_expr2 = M.delta * M.alpha_pick
    return (C10_expr1 - C10_expr2 <= 0)
M.ConstraintTenPicking = Constraint(M.TIMES)

       
# Constraint 11
def ConstraintEleven_rule(M, p, t):
    C11_expr1 = sum(M.x_vpt[v, p, t] for v in M.VENDORS)
    C11_expr1 -= sum(M.y_spt[s, p, t] for s in M.STORES)
    C11_expr2 = M.z_pt[p,t] - M.z_pt[p,M.T_minus_One[t]]

    return (C11_expr1 - C11_expr2 == 0)
M.ConstraintEleven = Constraint(M.PRODUCTS, M.TIMES)


# Constraint 12
def ConstraintTwelve_rule(M,s,p,t):
    C12_expr1 = M.y_spt[s, p, t] - M.r_spt[s,p,t]
    C12_expr1 -= M.d_spt[s,p,t] - M.r_spt[s,p,M.T_minus_One[t]]
    C12_expr2 = M.z_spt[s,p,t] - M.z_spt[s,p,M.T_minus_One[t]]

    return (C12_expr1 - C12_expr2 == 0)

M.ConstraintTwelve = Constraint(M.STORES, M.PRODUCTS, M.TIMES)


# Constraints 13
def ConstraintThirteen_rule(M, v, t):
    C13_expr1 = sum(M.V_p[p] * M.x_vpt[v, p, t] 
                         for p in M.PRODUCTS)
    C13_expr2 = M.ScriptQ * M.n_vt[v,t]                    
    return (C13_expr1 - C13_expr2 <= 0)
M.ConstraintThirteen = Constraint(M.VENDORS, M.TIMES)


# Constraints 14
def ConstraintFourteen_rule(M, s, t):
    C14_expr1 = sum(M.V_p[p] * M.y_spt[s, p, t] 
                         for p in M.PRODUCTS)
    C14_expr2 = M.ScriptQ * M.n_st[s,t]                    
    return (C14_expr1 - C14_expr2 <= 0)
M.ConstraintFourteen = Constraint(M.STORES, M.TIMES)


def Total_Cost_Objective_rule(M):
    return M.FirstStageCost + M.SecondStageCost

M.Total_Cost_Objective = Objective(sense=minimize)





