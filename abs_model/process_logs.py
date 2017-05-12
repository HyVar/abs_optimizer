import math

"""
process the logs of the hyvarsymexac simulator

Usage: .py <log file> prefix_of_output files
"""

import json
import sys
import logging
import os
import re
import getopt

TIME_SLICE = 60

components = []

def get_comp_num(s):
    global components
    n = int(s[4:])
    if n not in components:
        components.append(n)
    return n

def main(argv):
    """
    Main procedure
    """

    global map_name_id
    global map_id_name
    global mspl
    try:
        opts, args = getopt.getopt(argv,"hv",["help","verbose"])
    except getopt.GetoptError as err:
        print str(err)
        print(__doc__)
        sys.exit(1)
    for opt, arg in opts:
        if opt == '-h':
            print(__doc__)
            sys.exit()
        elif opt in ("-v", "--verbose"):
            logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.DEBUG)
            logging.info("Verbose output.")

    if len(args) != 2:
      print "2 argument are required"
      print(__doc__)
      sys.exit(1)

    log_file = os.path.abspath(args[0])
    prefix = args[1]

    scale_in = []
    scale_out = []
    jobs = []
    end = None
    fault = False

    with open(log_file, 'rb') as f:
        for line in f.readlines():
            if line.startswith("scale_in"):
                ls = line.split(",")
                scale_in.append((get_comp_num(ls[2]), int(ls[1]))) 
            elif line.startswith("scale_out"): 
                ls = line.split(",")
                scale_out.append((get_comp_num(ls[2]), int(ls[1])))
            elif line.startswith("job"):
                ls = line.split(",")
                jobs.append([ int(x) for x in ls[1:]])
            elif line.startswith("simulation_ended"):
                end = int(line.split(",")[1])
            elif line.startswith("FATAL"):
                fault = True

    # process scale decisions
    global components
    plus = {}
    minus = {}
    for i in components:
        plus[i] = { y: 0 for (x,y) in scale_in if x == i }
        minus[i] = { y: 0 for (x,y) in scale_out if x == i }
        for k in (plus[i].keys()):
          plus[i][k] = len(["" for (x,y) in scale_in if x == i and y == k])
        for k in (minus[i].keys()):
          minus[i][k] = len(["" for (x,y) in scale_out if x == i and y == k])
  
    components = sorted(components)
    logging.debug("Detected components " + unicode(components))
    logging.debug("Simulation ended at " + unicode(end))
    logging.debug("scale_in decisions : " + unicode(plus))
    logging.debug("scale_out decisions : " + unicode(minus))
    val = { x:0 for x in components }
    with open(prefix + "_vm.csv", "w") as f:
        f.write("time," + unicode([ "comp" + unicode(x) for x in components])[1:-1] + "\n")
        for i in range(0,end,TIME_SLICE):
            for j in components:
                for k in range(i,i+TIME_SLICE):
                  if k in plus[j]:
                      val[j] += plus[j][k]
                  if k in minus[j]:
                      val[j] -= minus[j][k]
            f.write( unicode(i) + "," + unicode([ val[x] for x in components])[1:-1]  + "\n")
    

    # process jobs
    jobs = sorted(jobs, key=lambda x: x[0])
    counter = 0
    with open(prefix + "_jobs.csv", "w") as f:
        f.write("job_id,start,end,latency")
        for i in range(len(jobs[0])-3):
            f.write(",comp" + unicode(i))
        f.write("\n")
        for i in jobs:
            f.write(unicode(counter))
            for j in i:
                f.write("," + unicode(j))
            f.write("\n")
            counter += 1

    # statistics
    max_latency = max([x[2] for x in jobs])
    logging.debug("number of jobs = " + unicode(len(jobs)))
    logging.debug("max latency = " + unicode(max_latency))

    return fault

                  
        

if __name__ == "__main__":
    main(sys.argv[1:])
