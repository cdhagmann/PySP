#-----------------------------------------------------------------------------
#                              IMPORT MODULES
#-----------------------------------------------------------------------------

from coopr.pyomo import AbstractModel, Set, Param, PositiveReals
from coopr.pyomo import NonNegativeIntegers, Binary, Var, summation

#-----------------------------------------------------------------------------
#                            MOTIVATION FROM WIFE
#-----------------------------------------------------------------------------

''' my husband is amazingly sexy! RAWR!! love, sara '''

#-----------------------------------------------------------------------------
#                           DECLARE MODEL constraintS
#-----------------------------------------------------------------------------


def objectiveA_rule(model):
    expr = model.Ca * (model.alpha_put + model.alpha_pick) + \
          model.Cth_put + model.Cth_pick
    return (expr, model.FirstStageCost)


def objectiveB_rule(model):
    expr = model.Ca * (model.alpha_put + model.alpha_pick) + \
          summation(model.Cth_put, model.theta_put) + \
          summation(model.Cth_pick, model.theta_pick)
    return (expr, model.FirstStageCost)


def objectiveC_rule(model):
    expr = sum((model.beta_put[t] + model.beta_pick[t])
               for t in model.TIMES) * model.Cb
    expr += sum(model.Cz_p[p] * model.z_pt[p, t]
                for p, t in model.PT)
    expr += sum(model.Cz_sp[s, p] * model.z_spt[s, p, t]
                for s, p, t in model.SPT)
    expr += sum(model.Cr_p[p] * model.r_spt[s, p, t]
                for s, p, t in model.SPT)
    expr += sum(model.Cf_v[v] * model.n_vt[v, t]
                for v, t in model.VT)
    expr += sum(model.Cf_s[s] * model.n_st[s, t]
                for s, t in model.ST)
    expr += sum(model.V_p[p] * model.Cv_v[v] * model.x_vpt[v, p, t]
                for v, p, t in model.VPT)
    expr += sum(model.V_p[p] * model.Cv_s[s] * model.y_spt[s, p, t]
                for s, p, t in model.SPT)
    return (expr, model.SecondStageCost)


def objective_rule(model):
    return model.FirstStageCost + model.SecondStageCost

def constraint1_rule(model):
    return (summation(model.theta_put), 1)


def constraint2_rule(model):
    return (summation(model.theta_pick), 1)


def constraint3_rule(model):
    expr = model.gamma * model.A_put - \
           model.alpha_put * model.Lambda_put
    return (None, expr, 0)


def constraint4_rule(model):
    expr = model.gamma * model.A_put - \
          summation(model.Lambda_put, model.zeta_put)
    return (None, expr, 0)


def constraint5_rule(model, i):
    expr = model.gamma * model.A_put * model.theta_put[i] - \
          model.alpha_put * model.Lambda_put[i]
    return (None, expr, 0)


def constraint6_rule(model):
    expr = model.gamma * model.A_pick - \
          model.alpha_pick * model.Lambda_pick
    return (None, expr, 0)


def constraint7_rule(model):
    expr = model.gamma * model.A_pick - \
          summation(model.Lambda_pick, model.zeta_pick)
    return (None, expr, 0)


def constraint8_rule(model, j):
    expr = model.gamma * model.A_pick * model.theta_pick[j] - \
          model.alpha_pick * model.Lambda_pick[j]
    return (None, expr, 0)


def constraint9_LB_rule(model, i):
    lower_bound = 0
    expr = model.zeta_put[i]
    return (lower_bound <= expr)


def constraint9_UB_rule(model, i):
    expr = model.zeta_put[i]
    upper_bound = model.M_alpha * model.theta_put[i]
    return (expr <= upper_bound)


def constraint10_LB_rule(model, i):
    lower_bound = 0
    expr = model.alpha_put - model.zeta_put[i]
    return (lower_bound <= expr)


def constraint10_UB_rule(model, i):
    expr = model.alpha_put - model.zeta_put[i]
    upper_bound = model.M_alpha * (1 - model.theta_put[i])
    return (expr <= upper_bound)


def constraint11_LB_rule(model, j):
    lower_bound = 0
    expr = model.zeta_pick[j]
    return (lower_bound <= expr)


def constraint11_UB_rule(model, j):
    expr = model.zeta_pick[j]
    upper_bound = model.M_alpha * model.theta_pick[j]
    return (expr <= upper_bound)


def constraint12_LB_rule(model, j):
    lower_bound = 0
    expr = model.alpha_pick - model.zeta_pick[j]
    return (lower_bound <= expr)


def constraint12_UB_rule(model, j):
    expr = model.alpha_pick - model.zeta_pick[j]
    upper_bound = model.M_alpha * (1 - model.theta_pick[j])
    return (expr <= upper_bound)


def constraint13_rule(model, t):
    expr1 = sum(model.x_vpt[v, p, t] for v, p in model.VP)
    expr2 = model.Lambda_put * (model.alpha_put +
                                model.eta_put * model.beta_put[t])
    return (expr1 <= expr2)


def constraint14_rule(model, t):
    expr1 = sum(model.x_vpt[v, p, t] for v, p in model.VP)
    expr2 = sum(model.Lambda_put[i] * (model.zeta_put[i] +
                model.eta_put * model.xi_put[i, t]) for i in model.PUTAWAY)
    return (expr1 <= expr2)


def constraint15_rule(model, i, t):
    expr1 = sum(model.x_vpt[v, p, t] for v, p in model.VP)
    expr2 = model.Lambda_put[i] * (model.alpha_put +
                                   model.eta_put * model.beta_put[t])
    upper_bound = model.BigM * (1 - model.theta_put[i])
    return (expr1 - expr2 <= upper_bound)


def constraint16_rule(model, t):
    expr1 = sum(model.y_spt[s, p, t] for s, p in model.SP)
    expr2 = model.Lambda_pick * (model.alpha_pick +
                                 model.eta_pick * model.beta_pick[t])
    return (expr1 <= expr2)


def constraint17_rule(model, t):
    expr1 = sum(model.y_spt[s, p, t] for s, p in model.SP)
    expr2 = sum(model.Lambda_pick[j] * (model.zeta_pick[j] +
                model.eta_pick * model.xi_pick[j, t]) for j in model.PICKING)
    return (expr1 <= expr2)


def constraint18_rule(model, j, t):
    expr1 = sum(model.y_spt[s, p, t] for s, p in model.SP)
    expr2 = model.Lambda_pick[j] * (model.alpha_pick +
                                   model.eta_pick * model.beta_pick[t])
    upper_bound = model.BigM * (1 - model.theta_pick[j])
    return (expr1 - expr2 <= upper_bound)


def constraint19_rule(model, t):
    return (model.beta_put[t] <= model.delta * model.alpha_put)


def constraint20_rule(model, t):
    return (model.beta_pick[t] <= model.delta * model.alpha_pick)


def constraint21_rule(model, p, t):
    tau = (t - 1) if (t - 1) in model.TIMES else len(model.TIMES)
    assert tau in model.TIMES

    expr1 = model.z_pt[p, t] - model.z_pt[p, tau]
    expr2 = sum(model.x_vpt[v, p, t] for v in model.VENDORS) - \
            sum(model.y_spt[s, p, t] for s in model.STORES)

    return (expr1 == expr2)


def constraint22_rule(model, s, p, t):
    tau = (t - 1) if (t - 1) in model.TIMES else len(model.TIMES)
    assert tau in model.TIMES

    expr1 = model.z_spt[s, p, t] - model.z_spt[s, p, tau]
    expr2 = model.y_spt[s, p, t] + model.r_spt[s, p, t]
    expr3 = model.d_spt[s, p, t] + model.r_spt[s, p, tau]

    return (expr1 == expr2 - expr3)


def constraint23_rule(model, v, t):
    expr = sum(model.V_p[p] * model.x_vpt[v, p, t] for p in model.PRODUCTS)
    return (expr <= model.ScriptQ * model.n_vt[v, t])


def constraint24_rule(model, s, t):
    expr = sum(model.V_p[p] * model.y_spt[s, p, t] for p in model.PRODUCTS)
    return (expr <= model.ScriptQ * model.n_st[s, t])


def constraint25_LB_rule(model, i, t):
    lower_bound = 0
    expr = model.xi_put[i, t]
    return (lower_bound <= expr)


def constraint25_UB_rule(model, i, t):
    expr = model.xi_put[i, t]
    upper_bound = model.M_beta * model.theta_put[i]
    return (expr <= upper_bound)


def constraint26_LB_rule(model, i, t):
    lower_bound = 0
    expr = model.beta_put[t] - model.xi_put[i, t]
    return (lower_bound <= expr)


def constraint26_UB_rule(model, i, t):
    expr = model.beta_put[t] - model.xi_put[i, t]
    upper_bound = model.M_beta * (1 - model.theta_put[i])
    return (expr <= upper_bound)


def constraint27_LB_rule(model, j, t):
    lower_bound = 0
    expr = model.xi_pick[j, t]
    return (lower_bound <= expr)


def constraint27_UB_rule(model, j, t):
    expr = model.xi_pick[j, t]
    upper_bound = model.M_beta * model.theta_pick[j]
    return (expr <= upper_bound)


def constraint28_LB_rule(model, j, t):
    lower_bound = 0
    expr = model.beta_pick[t] - model.xi_pick[j, t]
    return (lower_bound <=  expr)


def constraint28_UB_rule(model, j, t):
    expr = model.beta_pick[t] - model.xi_pick[j, t]
    upper_bound = model.M_beta * (1 - model.theta_pick[j])
    return (expr <= upper_bound)
