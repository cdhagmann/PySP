from coopr.pyomo import *
import constraints
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

model.STORES = Set()
model.PRODUCTS = Set()
model.VENDORS = Set()
model.TIMES = Set()
model.PICKING = Set()
model.PUTAWAY = Set()

model.SP = model.STORES * model.PRODUCTS
model.VP = model.VENDORS * model.PRODUCTS
model.ST = model.STORES * model.TIMES
model.PT = model.PRODUCTS * model.TIMES
model.VT = model.VENDORS * model.TIMES
model.VPT = model.VENDORS * model.PRODUCTS * model.TIMES
model.SPT = model.STORES * model.PRODUCTS * model.TIMES


model.Lambda_put = Param(model.PUTAWAY, within=PositiveReals)
model.Lambda_pick = Param(model.PICKING, within=PositiveReals)
model.Cth_put = Param(model.PUTAWAY, within=NonNegativeIntegers)
model.Cth_pick = Param(model.PICKING, within=NonNegativeIntegers)

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

model.Cr_p = Param(model.PRODUCTS, within=PositiveReals)

model.Ca = Param(within=PositiveReals)
model.Cb = Param(within=PositiveReals)

model.d_spt = Param(model.STORES, model.PRODUCTS, model.TIMES,
                    within=NonNegativeIntegers)

model.BigM = Param(within=NonNegativeIntegers, initialize=5000)
model.M_alpha = Param(within=NonNegativeIntegers, initialize=500)
model.M_beta = Param(within=NonNegativeIntegers, initialize=500)

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

#-----------------------------------------------------------------------------
#                           DECLARE MODEL CONSTRAINTS
#-----------------------------------------------------------------------------


model.FirstStageObjective = Constraint(rule=constraints.objectiveB_rule)
model.SecondStageObjective = Constraint(rule=constraints.objectiveC_rule)

model.Constraint1 = Constraint(rule=constraints.constraint1_rule)
model.Constraint2 = Constraint(rule=constraints.constraint2_rule)
model.Constraint5 = Constraint(model.PUTAWAY, rule=constraints.constraint5_rule)
model.Constraint8 = Constraint(model.PICKING, rule=constraints.constraint8_rule)
model.Constraint15 = Constraint(model.PUTAWAY, model.TIMES,
                                rule=constraints.constraint15_rule)
model.Constraint18 = Constraint(model.PICKING, model.TIMES,
                                rule=constraints.constraint18_rule)
model.Constraint19 = Constraint(model.TIMES, rule=constraints.constraint19_rule)
model.Constraint20 = Constraint(model.TIMES, rule=constraints.constraint20_rule)
model.Constraint21 = Constraint(model.PRODUCTS, model.TIMES,
                                rule=constraints.constraint21_rule)
model.Constraint22 = Constraint(model.STORES, model.PRODUCTS, model.TIMES,
                                rule=constraints.constraint22_rule)
model.Constraint23 = Constraint(model.VENDORS, model.TIMES,
                                rule=constraints.constraint23_rule)
model.Constraint24 = Constraint(model.STORES, model.TIMES,
                                rule=constraints.constraint24_rule)

model.Objective = Objective(rule=constraints.objective_rule)
