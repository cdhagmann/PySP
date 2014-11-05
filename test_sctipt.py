from instance_structure import InstanceStructure
from PySP import solve_ef_tech_model

data = InstanceStructure(3, 3, 3, 3, 3, 3, 3)
data.create_node_data()
data.create_scenario_data()

print solve_ef_tech_model(0, method='BigM')
print solve_ef_tech_model(0)
