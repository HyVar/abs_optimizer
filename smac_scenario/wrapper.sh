#!/bin/bash

# this program is called from the directory where the run command is

# For black box function optimization, we can ignore the first 5 arguments. 
# The remaining arguments specify parameters using this format: -name value 
#<algo executable> <instance name> <instance specific information> <cutoff time>
#  <cutoff length> <seed> <param> <param> <param>...

echo "Wrapper called from directory "`pwd`
cd ..
echo "Switching to directory "`pwd`
shift
shift
shift 
shift
shift
echo "run.py with parameters $@"
./run.py "$@"

