from pyomo.core import *

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
