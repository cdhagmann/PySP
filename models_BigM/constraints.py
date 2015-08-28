#-----------------------------------------------------------------------------
#                              IMPORT MODULES
#-----------------------------------------------------------------------------

from pyomo.core import *
from pyomo.core import AbstractModel, Set, Param, PositiveReals
from pyomo.core import NonNegativeIntegers, Binary, Var, summation
#-----------------------------------------------------------------------------
#                            MOTIVATION FROM WIFE
#-----------------------------------------------------------------------------

''' my husband is amazingly sexy! RAWR!! love, sara '''


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
model.PICKING = Set()
model.PUTAWAY = Set()


SP = model.STORES * model.PRODUCTS
VP = model.VENDORS * model.PRODUCTS
ST = model.STORES * model.TIMES
PT = model.PRODUCTS * model.TIMES
VT = model.VENDORS * model.TIMES
VPT = model.VENDORS * model.PRODUCTS * model.TIMES
SPT = model.STORES * model.PRODUCTS * model.TIMES


model.T_minus_One = Param(model.TIMES)

model.Lambda_put = Param(model.PUTAWAY, within=PositiveReals)
model.Lambda_pick = Param(model.PICKING, within=PositiveReals)
model.A_put = Param(within=PositiveReals)
model.A_pick = Param(within=PositiveReals)
model.gamma = Param(within=PositiveReals)
model.delta = Param(within=PositiveReals)
model.eta_put = Param(within=PositiveReals)
model.eta_pick = Param(within=PositiveReals)
model.ScriptQ = Param(within=PositiveReals)
model.V_p = Param(model.PRODUCTS, within=PositiveReals)
model.W_p = Param(model.PRODUCTS, within=PositiveReals)
model.Cf_v = Param(model.VENDORS, within=PositiveReals)
model.Cf_s = Param(model.STORES, within=PositiveReals)
model.Cv_v = Param(model.VENDORS, within=PositiveReals)
model.Cv_s = Param(model.STORES, within=PositiveReals)
model.Cz_p = Param(model.PRODUCTS, within=PositiveReals)
model.Cz_sp = Param(model.STORES, model.PRODUCTS, within=PositiveReals)
model.Cth_put = Param(model.PUTAWAY, within=PositiveReals)
model.Cth_pick = Param(model.PICKING, within=PositiveReals)
model.C_rp = Param(model.PRODUCTS, within=PositiveReals)
model.Ca = Param(within=PositiveReals)
model.Cb = Param(within=PositiveReals)
model.d_spt = Param(model.STORES, model.PRODUCTS, model.TIMES,
                    within=NonNegativeIntegers)

model.M_alpha = Param(within=NonNegativeIntegers, initialize=50)
model.M_beta = Param(within=NonNegativeIntegers, initialize=50)
model.BigM = Param(within=NonNegativeIntegers, initialize=5000)

#-----------------------------------------------------------------------------
#                           DECLARE MODEL VARIABLES
#-----------------------------------------------------------------------------

model.FirstStageCost = Var()
model.SecondStageCost = Var()

model.alpha_put = Var(bounds=(0.0, model.M_alpha),
                      within=NonNegativeIntegers)
model.alpha_pick = Var(bounds=(0.0, model.M_alpha),
                       within=NonNegativeIntegers)
model.theta_put = Var(model.PUTAWAY, within=Binary)
model.theta_pick = Var(model.PICKING, within=Binary)
model.lambda_put = Var(model.PUTAWAY, within=PositiveReals)
model.lambda_pick = Var(model.PICKING, within=PositiveReals)
model.beta_put = Var(model.TIMES, bounds=(0.0, model.M_beta),
                     within=NonNegativeIntegers)
model.beta_pick = Var(model.TIMES, bounds=(0.0, model.M_beta),
                      within=NonNegativeIntegers)
model.n_vt = Var(model.VENDORS, model.TIMES, within=NonNegativeIntegers)
model.n_st = Var(model.STORES, model.TIMES, within=NonNegativeIntegers)
model.x_vpt = Var(model.VENDORS, model.PRODUCTS, model.TIMES,
                  within=NonNegativeIntegers)
model.y_spt = Var(model.STORES, model.PRODUCTS, model.TIMES,
                  within=NonNegativeIntegers)
model.z_pt = Var(model.PRODUCTS, model.TIMES, within=NonNegativeIntegers)
model.z_spt = Var(model.STORES, model.PRODUCTS, model.TIMES,
                  within=NonNegativeIntegers)
model.r_spt = Var(model.STORES, model.PRODUCTS, model.TIMES,
                  within=NonNegativeIntegers)


# DUMMY VARIABLES

model.zeta_put = Var(model.PUTAWAY, bounds=(0.0, model.M_alpha),
                     within=NonNegativeIntegers)
model.zeta_pick = Var(model.PICKING, bounds=(0.0, model.M_alpha),
                      within=NonNegativeIntegers)

model.xi_put = Var(model.PUTAWAY, bounds=(0.0, model.M_alpha),
                   within=NonNegativeIntegers)
model.xi_pick = Var(model.PICKING, bounds=(0.0, model.M_alpha),
                    within=NonNegativeIntegers)
#-----------------------------------------------------------------------------
#                           DECLARE MODEL constraintS
#-----------------------------------------------------------------------------


def _objectiveA_rule(model):
    expr = model.Ca * (model.alpha_put + model.alpha_pick) + \
          model.Cth_put + model.Cth_pick
    return (expr, model.FirstStageCost)


def _objectiveB_rule(model):
    expr = model.Ca * (model.alpha_put + model.alpha_pick) + \
          summation(model.Cth_put, model.theta_put) + \
          summation(model.Cth_pick, model.theta_pick)
    return (expr, model.FirstStageCost)


def _objectiveC_rule(model):
    expr = sum((model.beta_put[t] + model.beta_pick[t])
               for t in model.TIMES) * model.Cb
    expr += sum(model.Cz_p[p] * model.z_pt[p, t]
                for p, t in PT)
    expr += sum(model.Cz_sp[s, p] * model.z_spt[s, p, t]
                for s, p, t in SPT)
    expr += sum(model.C_rp[p] * model.r_spt[s, p, t]
                for s, p, t in SPT)
    expr += sum(model.Cf_v[v] * model.n_vt[v, t]
                for v, t in VT)
    expr += sum(model.Cf_s[s] * model.n_st[s, t]
                for s, t in ST)
    expr += sum(model.V_p[p] * model.Cv_v[v] * model.x_vpt[v, p, t]
                for v, p, t in VPT)
    expr += sum(model.V_p[p] * model.Cv_s[s] * model.y_spt[s, p, t]
                for s, p, t in SPT)
    return (expr, model.SecondStageCost)


def _objective_rule(model):
    return model.FirstStageCost + model.SecondStageCost

def _constraint1_rule(model):
    return (summation(model.theta_put), 1)


def _constraint2_rule(model):
    return (summation(model.theta_pick), 1)


def _constraint3_rule(model):
    expr = model.gamma * model.A_put - \
           model.alpha_put * model.Lambda_put
    return (None, expr, 0)


def _constraint4_rule(model):
    expr = model.gamma * model.A_put - \
          summation(model.Lambda_put, model.zeta_put)
    return (None, expr, 0)


def _constraint5_rule(model, i):
    expr = model.gamma * model.A_put * model.theta_put[i] - \
          model.alpha_put * model.Lambda_put[i]
    return (None, expr, 0)


def _constraint6_rule(model):
    expr = model.gamma * model.A_pick - \
          model.alpha_pick * model.Lambda_pick
    return (None, expr, 0)


def _constraint7_rule(model):
    expr = model.gamma * model.A_pick - \
          summation(model.Lambda_pick, model.zeta_pick)
    return (None, expr, 0)


def _constraint8_rule(model, j):
    expr = model.gamma * model.A_pick * model.theta_pick[j] - \
          model.alpha_pick * model.Lambda_pick[j]
    return (None, expr, 0)


def _constraint9_LB_rule(model, i):
    lower_bound = 0
    expr = model.zeta_put[i]
    upper_bound = None
    return (lower_bound, expr, upper_bound)


def _constraint9_UB_rule(model, i):
    lower_bound = None
    expr = model.zeta_put[i]
    upper_bound = model.M_alpha * model.theta_put[i]
    return (lower_bound, expr, upper_bound)


def _constraint10_LB_rule(model, i):
    lower_bound = 0
    expr = model.alpha_put - model.zeta_put[i]
    upper_bound = None
    return (lower_bound, expr, upper_bound)


def _constraint10_UB_rule(model, i):
    lower_bound = None
    expr = model.alpha_put - model.zeta_put[i]
    upper_bound = model.M_alpha * (1 - model.theta_put[i])
    return (lower_bound, expr, upper_bound)


def _constraint11_LB_rule(model, j):
    lower_bound = 0
    expr = model.zeta_pick[j]
    upper_bound = None
    return (lower_bound, expr, upper_bound)


def _constraint11_UB_rule(model, j):
    lower_bound = None
    expr = model.zeta_pick[j]
    upper_bound = model.M_alpha * model.theta_pick[j]
    return (lower_bound, expr, upper_bound)


def _constraint12_LB_rule(model, j):
    lower_bound = 0
    expr = model.alpha_pick - model.zeta_pick[j]
    upper_bound = None
    return (lower_bound, expr, upper_bound)


def _constraint12_UB_rule(model, j):
    lower_bound = None
    expr = model.alpha_pick - model.zeta_pick[j]
    upper_bound = model.M_alpha * (1 - model.theta_pick[j])
    return (lower_bound, expr, upper_bound)


def _constraint13_rule(model, t):
    expr1 = sum(model.x_vpt[v, p, t] for v, p in VP)
    expr2 = model.Lambda_put * (model.alpha_put +
                                model.eta_put * model.beta_put[t])
    return (None, expr1, expr2)


def _constraint14_rule(model, t):
    expr1 = sum(model.x_vpt[v, p, t] for v, p in VP)
    expr2 = sum(model.Lambda_put[i] * (model.zeta_put[i] +
                model.eta_put * model.xi_put[i, t]) for i in model.PUTAWAY)
    return (None, expr1, expr2)


def _constraint15_rule(model, i, t):
    expr1 = sum(model.x_vpt[v, p, t] for v, p in VP)
    expr2 = model.Lambda_put[i] * (model.alpha_put +
                                   model.eta_put * model.beta_put[t])
    upper_bound = model.BigM * (1 - model.theta_put[i])
    return (None, expr1 - expr2, upper_bound)


def _constraint16_rule(model, t):
    expr1 = sum(model.y_spt[s, p, t] for s, p in SP)
    expr2 = model.Lambda_pick * (model.alpha_pick +
                                 model.eta_pick * model.beta_pick[t])
    return (None, expr1, expr2)


def _constraint17_rule(model, t):
    expr1 = sum(model.y_spt[s, p, t] for s, p in SP)
    expr2 = sum(model.Lambda_pick[j] * (model.zeta_pick[j] +
                model.eta_pick * model.xi_pick[j, t]) for j in model.PICKING)
    return (None, expr1, expr2)


def _constraint18_rule(model, j, t):
    expr1 = sum(model.y_spt[s, p, t] for s, p in SP)
    expr2 = model.Lambda_pick[j] * (model.alpha_pick +
                                   model.eta_pick * model.beta_pick[t])
    upper_bound = model.BigM * (1 - model.theta_pick[j])
    return (None, expr1 - expr2, upper_bound)


def _constraint19_rule(model, t):
    return (None, model.beta_put[t], model.delta * model.alpha_put)


def _constraint20_rule(model, t):
    return (None, model.beta_pick[t], model.delta * model.alpha_pick)


def _constraint21_rule(model, p, t):
    tau = (t - 1) if (t - 1) in model.TIMES else len(model.TIMES)
    assert tau in model.TIMES

    expr1 = model.z_pt[p, t] - model.z_pt[p, tau]
    expr2 = sum(model.x_vpt[v, p, t] for v in model.VENDORS) - \
            sum(model.y_spt[s, p, t] for s in model.STORES)

    return (expr1, expr2)


def _constraint22_rule(model, s, p, t):
    tau = (t - 1) if (t - 1) in model.TIMES else len(model.TIMES)
    assert tau in model.TIMES

    expr1 = model.z_spt[s, p, t] - model.z_spt[s, p, tau]
    expr2 = model.y_spt[s, p, t] + model.r_spt[s, p, t]
    expr3 = model.d_spt[s, p, t] + model.r_spt[s, p, tau]

    return (expr1, expr2 - expr3)


def constraint23_rule(model, v, t):
    expr = sum(model.V_p[p] * model.x_vpt[v, p, t] for p in model.PRODUCTS)
    return (None, expr, model.ScriptQ * model.n_vt[v, t])


def constraint24_rule(model, s, t):
    expr = sum(model.V_p[p] * model.y_vpt[s, p, t] for p in model.PRODUCTS)
    return (None, expr, model.ScriptQ * model.n_st[s, t])


def _constraint25_LB_rule(model, i, t):
    lower_bound = 0
    expr = model.xi_put[i, t]
    upper_bound = None
    return (lower_bound, expr, upper_bound)


def _constraint25_UB_rule(model, i, t):
    lower_bound = None
    expr = model.xi_put[i, t]
    upper_bound = model.M_beta * model.theta_put[i]
    return (lower_bound, expr, upper_bound)


def _constraint26_LB_rule(model, i, t):
    lower_bound = 0
    expr = model.beta_put[t] - model.xi_put[i, t]
    upper_bound = None
    return (lower_bound, expr, upper_bound)


def _constraint26_UB_rule(model, i, t):
    lower_bound = None
    expr = model.beta_put[t] - model.xi_put[i, t]
    upper_bound = model.M_beta * (1 - model.theta_put[i])
    return (lower_bound, expr, upper_bound)


def _constraint27_LB_rule(model, j, t):
    lower_bound = 0
    expr = model.xi_pick[j, t]
    upper_bound = None
    return (lower_bound, expr, upper_bound)


def _constraint27_UB_rule(model, j, t):
    lower_bound = None
    expr = model.xi_pick[j, t]
    upper_bound = model.M_beta * model.theta_pick[j]
    return (lower_bound, expr, upper_bound)


def _constraint28_LB_rule(model, j, t):
    lower_bound = 0
    expr = model.beta_pick[t] - model.xi_pick[j, t]
    upper_bound = None
    return (lower_bound, expr, upper_bound)


def _constraint28_UB_rule(model, j, t):
    lower_bound = None
    expr = model.beta_pick[t] - model.xi_pick[j, t]
    upper_bound = model.M_beta * (1 - model.theta_pick[j])
    return (lower_bound, expr, upper_bound)















