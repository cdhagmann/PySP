%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
Documentation of SWITP Pyomo Model codes
by Christopher Hagmann

October 17, 2013
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%



Instance.py
--------------------
This script generates instances for the given indices S,V,P,I,J,T,K. If ran:

python Instance.py

It will do a default case of 50,50,50,10,10,5,10 respectively. This is close to the size
for which we are hoping to do. If ran:

python Instance.py [any character]

it will give the option to specify these indices through a terminal text input.




bash.py
-------------------
This script creates Python commands for the bash PySP commands.

PySP_runef(solver=SOLVER) <---> runef --solve --solver=SOLVER --model-directory=models --instance-directory=nodedata
PySP_runph(solver=SOLVER) <---> runph --solver=SOLVER --model-directory=models --instance-directory=nodedata

These just directly emulate the bash commands and returns the objective value

The following commands uses the above to solve the I x J subproblems using gurobi as the 
printing the optimal value and tech choice.

pyomo_runef(solver='gurobi')
pyomo_runph(solver='gurobi')


pdat.py
--------------------
This script just facilitates the generation of the nodedata files



Run.py
--------------------
This scripts generates cases of indices to try and creates a report that it stores in the 
Resutls folder.
