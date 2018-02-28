""" A collection of variables used by the various modules """

# path of the parameters file
PARAMETERS_FILE = "./params.pcs"

# path of the model containing the definition of the parameters to omptimize
MODEL = "./examples/hyvar/Settings.abs"

# list of the path of the additional abs programs needed to compile the
# abs program
# relative path can be used assuming the current directory is abs_optimizer
ADDITIONAL_ABS_FILES = [ "/examples/hyvar/HyVarSym.abs" ]

# clock limit to use for the erlang simulation (parameter -l)
# -1 if the -l option does not need to be used
CLOCK_LIMIT = -1

# timeout in seconds for the ABS simulation
TIMEOUT = 3600

# timeout during the computation to expect at least some output (seconds)
# check every
# if value is -1 the check is not performed and the program is assumed to be correct
OUTPUT_TIMEOUT = -1 #30
# times without any output to detect that simulation is hanging
ERROR_NUMBER = 2

