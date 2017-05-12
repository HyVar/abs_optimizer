#!/usr/bin/python
import sys
import time

# For black box function optimization, we can ignore the first 5 arguments. 
# The remaining arguments specify parameters using this format: -name value 

scale_up = 90 
scale_down = 10

for i in range(len(sys.argv)-1):  
    if (sys.argv[i] == '-scale_up'):
        scale_up = float(sys.argv[i+1])
    elif(sys.argv[i] == '-scale_down'):
        scale_down = float(sys.argv[i+1])   

result = - (scale_up - scale_down)
time.sleep(2)
# SMAC has a few different output fields; here, we only need the 4th output:
print "Result of algorithm run: SUCCESS, 0, 0, %d, 0" % result
