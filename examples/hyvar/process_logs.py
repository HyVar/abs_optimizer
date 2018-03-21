import math
import click
import os

"""
process the logs of the hyvar toolchain simulator
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

import requests as request_lib


COMP_LOG_FILENAMES = {
    'encoder': "encoder",
    'hyvarrec': "hyvarrec",
    'decoder': "decoder",
    'resolution_spl': "implementation_resolution",
    #'resolution_conf': {"scaling": "code_generator_haproxy_scaling.log", "haproxy": "code_generator_haproxy_updater.log"},
    'variant_gen': "variant_generator",
    'code_gen': "code_generator",
    'c_compiler': "tarballgenerator",
    'java_compiler': "java_compiler",
}

SCALING_LOG_SUFFIX = "_scaling.log"
HAPROXY_LOG_SUFFIX = "_haproxy_updater.log"

JOB_LOG_FILENAME_SUFFIX = "requestmetrics.csv"
GLOBAL_COMPONENT_NAME = "__global__"

def parse_time_stamp(s):
    # given a time in format '%Y-%m-%d %H:%M:%S,%f' return the seconds from the beginning of epoch
    return time_import.mktime(time_import.strptime(s,'%Y-%m-%d %H:%M:%S,%f'))


def parse_jobs_log(lines):
    """
    Parses the log of all the jobs. Prints some info if info verbose modality is activated
    Returns the bounds of the temporal windows to consider to parse the other logs
    """
    # parse first line to get the ids
    ls = lines.pop(0).split("|")
    map_ids = {}
    for i in range(0,len(ls)):
        map_ids[ls[i]] = i

    total_time = {}
    start_time = {}
    end_time = {}

    if not lines:
        logging.critical("No jobs found in jobs logs. Exiting")
        sys.exit(1)
    for line in lines:
        if line:
            ls = line.split("|")
        id = int(ls[map_ids["id"]])
        total_time[id] = int(ls[map_ids["total_time"]])
        time_string = ls[map_ids["start_ts"]].split(".")[0].replace("+00","")
        start_time[id] = time_import.mktime(
            time_import.strptime(time_string,'%Y-%m-%d %H:%M:%S'))
        time_string = ls[map_ids["end_ts"]].split(".")[0].replace("+00", "")
        end_time[id] = time_import.mktime(
            time_import.strptime(time_string,'%Y-%m-%d %H:%M:%S'))
    logging.info("Number of jobs: {}".format(len(total_time)))
    logging.info("Average solving time: {}".format(sum(total_time.values())/len(total_time)))
    min_time = int(min(start_time.values()))
    max_time = int(max(end_time.values()))
    logging.info("Min time: {}".format(min_time))
    logging.info("Max time: {}".format(max_time))

    logging.debug("Computing request and latencies per minute")
    latencies = {int(math.floor(float(i) / 60)): 0 for i in range(0,(max_time-min_time)+59, 60)}
    counters = {int(math.floor(float(i) / 60)): 0 for i in range(0,(max_time-min_time)+59, 60)}
    requests = {int(math.floor(float(i) / 60)): 0 for i in range(0,(max_time-min_time)+59, 60)}
    for i in total_time:
        requests[int(math.floor(float(start_time[i] - min_time) / 60))] += 1
        counters[int(math.floor(float(end_time[i] - min_time) / 60))] += 1
        latencies[int(math.floor(float(end_time[i] - min_time) / 60))] += total_time[i]
    for i in counters:
        if counters[i] > 0:
            latencies[i] = int(float(latencies[i]) / counters[i])
    return min_time, max_time, latencies, requests


def parse_haproxy_updater_log(lines,starting_time=0, ending_time=0):
    """
    Collects the number of instances every minute parsing the haproxy updater log
    Returns two dictionaries with entries: { minute: latency } and { minute: response_num }
    """
    instance_count = {}
    for row in lines:
        m = re.match("(.*):INFO:(.*)", row)
        if row and m:
            time = parse_time_stamp(m.group(1))
            if starting_time <= time <= ending_time:
                time = int(math.floor(float(time - starting_time) / 60))
                message = m.group(2)
                m = re.match("scaling_tools:Healthy instance\(s\): \[(.*)\]", message)
                if m:
                    ips = m.group(1)
                    ls = re.findall("'[0-9\.]*'",ips)
                    instance_count[time] = len(ls)
                else:
                    m = re.match("(__main__:No difference between healthy instances and enabled instances in HAProxy config)" +
                                 "|(haproxy:Restarted HAProxy)" +
                                 "|(haproxy:Updating HAProxy config with instances.*)" +
                                 "|(scaling_tools:Unhealthy instance.*)" +
                                 "|(__main__:Enabled [0-9]+ server\(s\))" +
                                 "|(__main__:Disabled.*)", message)
                    if m is None:
                        logging.warning("HAProxy updater log not recognized: <<<{}>>>".format(message))

    logging.debug("Instance count dict: {}".format(instance_count))
    return instance_count

def parse_scaling_log(lines,starting_time=0,ending_time=0):
    """
    Collects the latency and number of responses every minute parsing the scaling log
    Returns two dictionaries with entries: { minute: latency } and { minute: response_num }
    """
    requests_count = {}
    averages = {}
    for row in lines:
        m = re.match("(.*):INFO:__main__:(.*)",row)
        if row and m:
            time = parse_time_stamp(m.group(1))
            if starting_time <= time <= ending_time:
                time = int(math.floor(float(time - starting_time) / 60))
                message = m.group(2)
                m = re.match("([0-9]+) latency measurements found in the last minute", message)
                if m:
                    requests_count[time] = int(m.group(1))
                else:
                    m = re.match("Average latency for the last minute is ([0-9]+) ms", message)
                    if m:
                        averages[time] = int(m.group(1))
                    else:
                        m = re.match("(Average latency for the last [0-9]+ minutes is [0-9]+ ms)" +
                                     "|(Last scaling action was less then [0-9]+ minute\(s\) ago, no more actions allowed yet)" +
                                     "|([0-9]+ latency measurements found in the last [0-9]+ minutes)" +
                                     "|(No loads and latencies, doing nothing)" +
                                     "|(Average latency [0-9]+ is above high threshold of [0-9]+ seconds)" +
                                     "|(Average latency [0-9]+ is below low threshold of [0-9]+ seconds)" +
                                     "|(Detaching instances \[.*\])" +
                                     "|(Terminated detached instances \[.*\])",
                                     message)
                        if m is None:
                            logging.warning("Scaling log not recognized: <<<{}>>>".format(message))

    # average is 0 if no value has been found for a given time frame
    for i in requests_count:
        if i not in averages:
            averages[i] = 0

    logging.debug("Request count dict: {}".format(requests_count))
    logging.debug("Average dict: {}".format(averages))
    return requests_count, averages


@click.command()
@click.option('--logs-dir',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=False, readable=True, resolve_path=True),
    default="./",
    help='The directory where the log files are stored.')
# @click.option('--jobs-out-file',
#     type=click.Path(exists=False, file_okay=True, dir_okay=False, writable=True, readable=True, resolve_path=True),
#     default=None,
#     help='The cvs log files containing the vm info.')
# @click.option('--vm-out-file',
#     type=click.Path(exists=False, file_okay=True, dir_okay=False, writable=True, readable=True, resolve_path=True),
#     default=None,
#     help='The cvs log files containing the vm info.')
@click.option('--send-data',
              is_flag=True,
              help='Send data to ABS Erlang simulation.')
@click.option('--port',
    type=click.INT,
    default=8080,
    help='Port used by the Erlang ABS server to run the simulation. Default 8080')
@click.option('--url',
    type=click.STRING,
    help='Url used by the Erlang ABS server to run the simulation. Default http://localhost',
    default="http://localhost"
    )
@click.option('--sleep-time',
              type=click.FLOAT,
              default=0,
              help='Time in seconds to sleep between get requests.')
@click.option('--verbose', '-v',
              count=True,
              help="Print debug messages.")
def main(port,
         logs_dir,
         verbose,
         send_data,
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

    # dictionaries to store the important data
    latencies = {}
    requests = {}
    instances = {}

    file_name = [os.path.join(logs_dir,x) for x in os.listdir(logs_dir) if x.endswith(JOB_LOG_FILENAME_SUFFIX)]
    if file_name:
        file_name = file_name[0]
    else:
        logging.critical("No {} file found in directory {}".format(JOB_LOG_FILENAME_SUFFIX,logs_dir))
        sys.exit(1)

    logging.info("Parsing jobs file {}".format(file_name))
    if not os.path.isfile(file_name):
        logging.critical("File {} not found. Exiting.".format(file_name))
        sys.exit(1)
    with open(file_name,'rb') as f:
        lines = f.readlines()
        min_time, max_time, latencies[GLOBAL_COMPONENT_NAME], requests[GLOBAL_COMPONENT_NAME] = parse_jobs_log(lines)

    for c in COMP_LOG_FILENAMES:

        file_name = [x for x in os.listdir(logs_dir) if x.endswith(COMP_LOG_FILENAMES[c] + SCALING_LOG_SUFFIX)]
        if not file_name:
            logging.critical("File {} not found. Exiting.".format(file_name))
            sys.exit(1)
        file_name = os.path.join(logs_dir, file_name[0])
        logging.debug("Parsing file {}".format(file_name))
        with open(file_name,'rb') as f:
            lines = f.readlines()
            requests[c], latencies[c] = parse_scaling_log(lines,min_time,max_time+60)

        file_name = [x for x in os.listdir(logs_dir) if x.endswith(COMP_LOG_FILENAMES[c] + HAPROXY_LOG_SUFFIX)]
        if not file_name:
            logging.critical("File {} not found. Exiting.".format(file_name))
            sys.exit(1)
        file_name = os.path.join(logs_dir, file_name[0])
        logging.debug("Parsing file {}".format(file_name))
        with open(file_name,'rb') as f:
            lines = f.readlines()
            instances[c] = parse_haproxy_updater_log(lines,min_time,max_time+60)

    # sum up all the instances for the global component
    instances[GLOBAL_COMPONENT_NAME] = {}
    for i in requests[GLOBAL_COMPONENT_NAME]:
        counter = 0
        for j in COMP_LOG_FILENAMES:
            if i in instances[j]:
                counter += instances[j][i]
            else:
                instances[j][i] = instances[j][i-1] if i-1 in instances[j] else 0
                logging.warning("Not found number of instances for component {} at minute {}. Assigning previous value {}".format(
                    j, i, instances[j][i]))

        instances[GLOBAL_COMPONENT_NAME][i] = counter
    logging.info("Average number of virtual machines: {}".format(
        float(sum(instances[GLOBAL_COMPONENT_NAME].values())/len(instances[GLOBAL_COMPONENT_NAME]))))

    if send_data:

        # logging.info("Resetting")
        # for c in ["component_" + x for x in COMP_LOG_FILENAMES] + [GLOBAL_COMPONENT_NAME]:
        #     r = request_lib.get("{}:{}/call/{}/reset_real_history".format(url,port,c))
        #     if r.status_code != 200:
        #         logging.warning("GET request at {} failed with code {}: {}".format(r.url, r.status_code, r.text))
        #     if sleep_time:
        #         time.sleep(sleep_time)
        logging.info("Sending real data to ABS simulation")

        for c in COMP_LOG_FILENAMES:
            data = {
                "instances": [instances[c][i] for i in sorted(instances[c])],
                "latency": [latencies[c][i] for i in sorted(latencies[c])],
                "requests": [requests[c][i] for i in sorted(requests[c])]
            }

            r = request_lib.get("{}:{}/call/component_{}/add_real_info_at_once".format(url, port, c),
                                data=json.dumps(data))
            if r.status_code != 200:
                logging.warning("GET request at {} failed with code {}: {}".format(r.url,r.status_code, r.text))
            if sleep_time:
                time.sleep(sleep_time)

        # update global component
        c = GLOBAL_COMPONENT_NAME
        data = {
            "instances": [instances[c][i] for i in sorted(instances[c])],
            "latency": [latencies[c][i] for i in sorted(latencies[c])],
            "requests": [requests[c][i] for i in sorted(requests[c])]
        }

        r = request_lib.get("{}:{}/call/{}/add_real_info_at_once".format(url, port, c),
                                data=json.dumps(data))
        if r.status_code != 200:
            logging.warning("GET request at {} failed with code {}: {}".format(r.url, r.status_code, r.text))

if __name__ == "__main__":
    main()