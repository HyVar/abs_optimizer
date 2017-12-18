#!/usr/bin/python  
"""
Module defining the function compute_quality that parses the output
of the ABS program and returns a value (float) representing the solution quality.
"""

import os
import sys
sys.path.append("./abs_model")
import process_logs
import uuid

def parse_rat(s):
    ls = map( lambda x: int(x), s.split('/'))
    if len(ls) > 1:
        return ls[0] / ls[1]
    else:
        return ls[0]

def compute_quality(out):

    out_file = '/tmp/' + uuid.uuid4().hex + ".log"
    with open(out_file,"w") as f:
        f.write(out)

    prefix = '/tmp/' + uuid.uuid4().hex
    fault = process_logs.main([out_file,prefix])

    if fault:
        raise Exception("Detected an error of the ABS backend")
    
    summatory = 0
    counter = 0
    with open(prefix + "_jobs.csv", 'r') as f:
        lines = f.readlines()[1:]

    for line in lines:
        counter += 1
        summatory += int(line.split(",")[3])
          
    average_latency = float(summatory) / counter

    print "Average latency: " + unicode(average_latency)

    with open(prefix + "_vm.csv", 'r') as f:
        lines = f.readlines()[1:]

    ls = [ int(x.strip()) for x in lines[0].replace("\n", "").split(",")]
    time = ls[0]  
    summatory = 0
    
    for line in lines[1:]:
        ls = [ int(x.strip()) for x in line.replace("\n", "").split(",")]
        summatory += sum(ls[1:]) * (ls[0] - time)
        time = ls[0]

    summatory = float(summatory) / time

    os.remove(prefix + "_vm.csv")
    os.remove(prefix + "_jobs.csv")
    os.remove(out_file)

    print "Average instances per second: " + unicode(summatory)


    # interesting in latency < 300 seconds
    # we assume that no more than 300 machines are used in average
    if average_latency < 300000:
        summatory = summatory
        return summatory
    else:
        print "Violation of constraints"
        return average_latency/1000


# main procedure to test a sample given in input
def main(args):
    with open(args[0],"r") as f:
        return compute_quality(f.read())

if __name__ == "__main__":
    main(sys.argv[1:])
