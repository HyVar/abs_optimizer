#!/usr/bin/python  
"""
run.py -param_name_1 value_1 ... -param_name_n value_n
"""

import re
import os
import sys
import logging as log
import time
import uuid
import shutil
import fcntl

import settings
import parse_abs_output

log.basicConfig(format="%(levelname)s: %(message)s", level=log.DEBUG)

from subprocess import Popen, PIPE

def read_lines(proc):
    """
    Returns the stream of the read lines of a process.
    """
    try:
      return proc.stdout.read()
    except:
      return ''


def change_parameters(lines,parameters):
    for i in range(len(lines)):  
        m = re.match("def\s*(Int|Rat)\s*([a-zA-Z0-9_]*).*=.*",lines[i])
        if m is not None:
            if m.group(2) in parameters:
                log.info("changed parameter " + m.group(2) + " to " + unicode(parameters[m.group(2)]))
                lines[i] = "def " + m.group(1) + " " + m.group(2) + "() = " + unicode(parameters[m.group(2)]) + ";\n"

def main(argv):

    with open(settings.PARAMETERS_FILE, 'r') as f:
        lines = f.readlines();
    
    # parsing parameters in the parameter file
    # todo: consider also ordinal and categorical parameters
    parameters = {}
    for i in lines:
        # expression to match
        # <parameter_name> integer [<min value>, <max value>] [<default value>] [log]
        m = re.match("([a-zA-Z_0-9]*)\s+integer\s+\[\s*-?[0-9]+\s*\,\s*-?[0-9]+\s*\]\s*\[\s*(-?[0-9]+)\s*\].*",i)
        if m is not None:
            log.info("Found parameter " + m.group(1))
            parameters[m.group(1)] = int(m.group(2))
        else:
            # <parameter_name> ordinal { ... } [<default value>] [log]
            m = re.match("([a-zA-Z_0-9]*)\s+ordinal\s+\{.*\}\s*\[\s*(-?[0-9]+)\s*\].*",i)
            if m is not None:
                log.info("Found parameter " + m.group(1))
                parameters[m.group(1)] = int(m.group(2))

    # parse the input prameters
    for i in range(0,len(argv),2):  
        m = re.match('-([a-zA-Z_0-9]*)',argv[i])
        if m is not None:
            if m.group(1) not in parameters:
                print 'Result of this algorithm run: CRASHED, 0, 0, ' + \
                    '0, 0, "Parameter ' + m.group(1) + ' not found"'
                exit(1)
            else:
                log.info("Detected in input the parameter " + m.group(1))
                parameters[m.group(1)] = argv[i+1]
        else:
            print 'Result of this algorithm run: CRASHED, 0, 0, 0' + \
                  ', 0, "Parameter ' + argv[i] + ' not found"'
            exit(1)


    new_dir = '/tmp/' + uuid.uuid4().hex
    os.makedirs(new_dir)
    new_model = new_dir + '/' + uuid.uuid4().hex + '.abs'

    log.info('Generating new model')
    with open(settings.MODEL, 'r') as f:
        lines = f.readlines()    
    change_parameters(lines,parameters)
    with open(new_model,'w') as f:
        f.writelines(lines)
    
    log.info('Compiling model')
    proc = Popen( ["absc", "-erlang", new_model] + 
                  [os.path.abspath(x) for x in settings.ADDITIONAL_ABS_FILES],
          stdout=PIPE, stderr=PIPE, cwd=new_dir )
    out, err = proc.communicate()
    log.debug('Stdout of abs compilation')
    log.debug(out)
    log.debug('Stdout of abs compilation')
    log.debug(err)

    log.info('Running model')
    start_time = time.time()
    if settings.CLOCK_LIMIT == -1:
        proc = Popen( [ "timeout", unicode(settings.TIMEOUT), 
                  "./gen/erl/run" ],
          stdout=PIPE, stderr=PIPE, cwd=new_dir )
    else:
        proc = Popen( [ "timeout", unicode(settings.TIMEOUT), 
                  "./gen/erl/run", "-l", unicode(settings.CLOCK_LIMIT) ],
          stdout=PIPE, stderr=PIPE, cwd=new_dir )
    # non blocking reads
    fd = proc.stdout.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
    
    last_out = "no_empy"    
    out = ""    
    while proc.poll() is None and last_out:
        time.sleep(settings.OUTPUT_TIMEOUT)
        last_out = read_lines(proc)
        #print "<" + last_out + ">"
        out += last_out
    if proc.poll() is None:
        proc.kill()
    else:
        out += proc.stdout.read()
    #out, err = proc.communicate()
    run_time = time.time() - start_time
    log.debug('Stdout of abs compilation')
    log.debug(err)

    shutil.rmtree(new_dir)

    try:
        quality = parse_abs_output.compute_quality(out)
        print 'Result of this algorithm run: SAT, 0, 0, ' + unicode(quality) + ', 0'
    except Exception:
        print 'Result of this algorithm run: CRASHED, 0, 0, 0, 0, "Metric evaluation problem"'

if __name__ == "__main__":
    if 'run.py' in sys.argv[0]:
        main(sys.argv[1:])
    else:
        main(sys.argv[2:])
