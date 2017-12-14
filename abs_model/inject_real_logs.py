import math
import click
import os

"""
process the logs of the hyvarsymexac simulator

Usage: .py <log job file> <log vm file> <prefix_of_output files>
"""

import json
import sys
import logging
import os
import re
import getopt
import time as time_import
import math
import time

import requests


#import generate_settings



components = []

def get_comp_num(s):
    global components
    n = int(s[4:])
    if n not in components:
        components.append(n)
    return n


def parse_time_stamp(s):
    return time_import.mktime(time_import.strptime(s.split(".")[0], '%Y-%m-%d %H:%M:%S'))

@click.command()
@click.option('--jobs-file',
    type=click.Path(exists=True, file_okay=True, dir_okay=False, writable=False, readable=True, resolve_path=True),
    default="./jobs.log",
    help='The cvs log files containing the jobs info.')
@click.option('--vm-file',
    type=click.Path(exists=True, file_okay=True, dir_okay=False, writable=False, readable=True, resolve_path=True),
    default="./vm.log",
    help='The cvs log files containing the vm info.')
@click.option('--jobs-out-file',
    type=click.Path(exists=False, file_okay=True, dir_okay=False, writable=True, readable=True, resolve_path=True),
    default=None,
    help='The cvs log files containing the vm info.')
@click.option('--vm-out-file',
    type=click.Path(exists=False, file_okay=True, dir_okay=False, writable=True, readable=True, resolve_path=True),
    default=None,
    help='The cvs log files containing the vm info.')
@click.option('--send-data',
              is_flag=True,
              help='Send data to ABS Erlang simulation.')
@click.option('--port',
    type=click.INT,
    default=8080,
    help='Port used by the Erlang ABS server to run the simulation.')
@click.option('--url',
    type=click.STRING,
    default="http://localhost",
    help='Url used by the Erlang ABS server to run the simulation.')
@click.option('--time-slice',
              type=click.INT,
              default=60,
              help='Time in seconds to consider for computing the average.')
@click.option('--sleep-time',
              type=click.FLOAT,
              default=0,
              help='Time in seconds to sleep between get requests.')
@click.option(
	'--verbose', '-v',
	count=True,
	help="Print debug messages.")
def main(port,
         jobs_file,
         vm_file,
         verbose,
         time_slice,
         send_data,
         jobs_out_file,
         vm_out_file,
         sleep_time,
         url):

    log_level = logging.ERROR
    if verbose == 1:
        log_level = logging.WARNING
    elif verbose == 2:
        log_level = logging.INFO
    elif verbose >= 3:
        log_level = logging.DEBUG
    logging.basicConfig(format="%(levelname)s: %(message)s", level=log_level)
    logging.info("Verbose Level: " + unicode(verbose))
    logging.basicConfig(level=log_level)

    logging.info("Parsing the job log files")
    time_min = None
    time_max = None

    with open(jobs_file, 'rb') as f:
        lines = f.readlines()

    job_log_header = [x.strip() for x in lines.pop(0).replace("\n","").split("|")]

    important_times = {}
    for line in lines:
        if line.strip():
            ls = [x.strip() for x in line.replace("\n","").split("|")]
            start_time = parse_time_stamp(ls[job_log_header.index("start_ts")])
            time_min = min(start_time,time_min) if time_min else start_time
            end_time = parse_time_stamp(ls[job_log_header.index("end_ts")])
            time_max = max(end_time, time_max) if time_max else end_time
            important_times[int(ls[job_log_header.index("client_id")])] = {
                "start_time": start_time,
                "end_time": end_time,
                "total_time": int(ls[job_log_header.index("total_time")])
            }

    logging.info("time min = {}".format(time_min))
    logging.info("time max = {}".format(time_max))
    logging.info("Shifting times to beginning of time")
    for i in important_times:
        important_times[i]["start_time"] -= time_min
        important_times[i]["end_time"] -= time_min
    
    # parse the vm log file
    # vm = {}
    # keys = set() # list of components
    # states = set() # list of state of components
    # with open(vm_file, 'rb') as f:
    #     lines = f.readlines()
    #     for line in lines[1:]:
    #         if line.strip():
    #             ls = [x.strip() for x in line.replace("\n","").split("|")]
    #             time = parse_time_stamp(ls[1])
    #             if time <= time_max and time >= time_min:
    #                 vm[time] = json.loads(ls[3])
    #                 data = json.loads(ls[2])
    #                 for i in vm[time].keys():
    #                     vm[time][i] = vm[time][i].values()
    #                     vm[time][i] += data[i].values()
    #                     states.update(vm[time][i])
    #                 keys.update(vm[time].keys())


    # write jobs csv file
    # with open()

    # keys = list(keys)
    # states = list(states)
    # with open(prefix + "_vm.csv", "w") as f:
    #     f.write("time")
    #     for i in keys:
    #         for j in states:
    #             f.write("," + i + "___" + j)
    #     f.write(",timestamp\n")
    #     for time in sorted(vm.keys()):
    #         f.write(unicode(time))
    #         for i in keys:
    #             for j in states:
    #                 f.write("," + unicode(len([ x for x in vm[time][i] if x == j])))
    #         f.write("," +   time_import.strftime("%a, %d %b %Y %H:%M:%S +0000", time_import.gmtime(int(time))))
    #         f.write("\n")

    logging.info("Computing the average latency")
    counters = {}
    for i in range(0,int((time_max-time_min)/time_slice) + 1):
        counters[i] = {"arrivals": 0, "responses": 0, "total_time": 0}
    for i in important_times:
        counters[int(important_times[i]["start_time"] / time_slice)]["arrivals"] += 1
        counters[int(important_times[i]["end_time"] / time_slice)]["responses"] += 1
        counters[int(important_times[i]["end_time"] / time_slice)]["total_time"] += important_times[i]["total_time"]
     # f.write("{},{},{},{}\n".format(i*TIME_SUM_WINDOW,sum_arrival[i],sum_response[i],sum_tar_arrival[i]))

    logging.debug("There are {} time intervals".format(len(counters)))
    logging.debug(unicode(counters))
    if send_data:
        logging.info("Sending data to ABS simulation")

        for i in sorted(counters.keys()):
            r = requests.get("{}:{}/call/__global__/add_real_info?latency={}&instances={}".format(
                url,
                port,
                counters[i]["total_time"]/counters[i]["responses"] if counters[i]["responses"] else 0,
                1))
            if r.status_code != 200:
                logging.warning("GET request at {} failed with code {}: {}".format(r.url,r.status_code, r.text))
            if sleep_time:
                time.sleep(sleep_time)

if __name__ == "__main__":
    main()