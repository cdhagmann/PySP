from instance_structure import InstanceStructure
from PySP import GBB, RLT, BigM
from Function_Module import perc, curr, ptime

data = InstanceStructure(3, 3, 3, 3, 3, 3, 3)
data.create_node_data()
data.create_scenario_data()


obj, t = BigM('PH')
n = len(str(obj)) + 3
print 'BigM/PH - {0:{2}} {1}'.format(curr(obj), ptime(t), n)
obj, t = RLT('PH')
print 'RLT/PH  - {0:{2}} {1}'.format(curr(obj), ptime(t), n)
obj, t = BigM('EF')
print 'BigM/EF - {0:{2}} {1}'.format(curr(obj), ptime(t), n)
obj, t = RLT('EF')
print 'RLT/EF  - {0:{2}} {1}'.format(curr(obj), ptime(t), n)
obj, t = GBB()
print 'GBB/EF  - {0:{2}} {1}'.format(curr(obj), ptime(t), n)
