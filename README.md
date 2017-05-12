# ABS parameter optimizer

This program allows the optimization of some parameters of an ABS model by using the
algorithm configurator SMAC.

In order to use this tool you have to:
- define all the parameters in one ABS module or program. The parameter
named X has to be defined in a unique line of ABS code as follows.

```
def Int X() = 0;
```

We invite the user to store all the ABS files in the abs_model folder.

- define all the parameters to optimize with their range, default value,
and limitations in the file params.pcs . The format to use for defining
the parameters is exactly the one used by the SMAC tool.  Please see
http://www.cs.ubc.ca/labs/beta/Projects/SMAC/v2.10.03/manual.pdf for more
details.

- define the scenario setting to use SMAC in the file scenario.txt . In
particular an important element that may be changes is the number of runs
of the models which is selected by setting the parameter numberOfRunsLimit.
For the meaning of the other parameters we invite the user to consult the
manual of SMAC.

- define the quality of a run of the ABS model. The function to compute the
quality based on the output of the ABS simulation is defined by means of a
python program in the program parse_abs_output.py

- define the settings related to the ABS simulation (e.g., which model contains
the parameters, what are the other ABS file to use for the compilation,
timeouts, ...) in the file settings.py

The tool can be run by invoking the command run_smac.sh
The output of the computation is saved in the directory smac-output
