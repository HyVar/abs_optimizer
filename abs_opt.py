"""
This program can be used to trigger the optimization of an abs model
"""
import datetime
import os
import numpy
import logging
import click
import json
import sys
import multiprocessing
import tempfile
import re
import requests
import time

# Import ConfigSpace and different types of parameters
from smac.configspace import ConfigurationSpace
from ConfigSpace.hyperparameters import CategoricalHyperparameter, \
    OrdinalHyperparameter, UniformIntegerHyperparameter

# Import SMAC-utilities
from smac.tae.execute_func import ExecuteTAFuncDict
from smac.scenario.scenario import Scenario
from smac.facade.smac_facade import SMAC

DEFAULT_SCENARIO = {"run_obj": "quality",
                    "deterministic": "true",
                    "shared_model": "true",
                    "initial_incumbent": "RANDOM",
                    "abort_on_first_run_crash": "True",
                    }
ABS_FILES = []
LOG_PARSER_PROGRAM = os.path.join(os.getcwd(),"solution_quality.py")
SERVER_URL = "http://localhost"
SERVER_PORT = "9001"
SERVER_HOST = ""

SLEEP_TIME_AFTER_ERROR = 60
RESUBMISSION_ATTEMPTS = 2

@click.group()
@click.option('--log-level',
              help='Log level',
              type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
              show_default=True,
              default="DEBUG")
def cli(log_level):
    # Configure logging
    logging.basicConfig(format="[%(asctime)s][%(levelname)s][%(name)s]%(message)s",
                        level=log_level)




################################
# Utility functions
################################
def build_config_space(data):
    # Build Configuration Space which defines all parameters and their ranges
    cs = ConfigurationSpace()

    params = {}

    for i in data["parameters"]:
        obj = data["parameters"][i]
        if obj["type"] == "integer":
            if min(obj["values"]) < max(obj["values"]):
                params[i] = UniformIntegerHyperparameter(
                    i, min(obj["values"]), max(obj["values"]), default_value=obj["default"])
                cs.add_hyperparameter(params[i])
            else:
                logging.warning("Parameter {} can take only one value. It will be ignored".format(i))
        elif obj["type"] == "ordinal":
            if len(obj["values"]) > 1:
                params[i] = OrdinalHyperparameter(i, obj["values"], default_value=obj["default"])
                cs.add_hyperparameter(params[i])
            else:
                logging.warning("Parameter {} can take only one value. It will be ignored".format(i))
        else:
            logging.critical("Parameter type {} for parameter {} not supported. Exiting".format(obj["type"],i))
            sys.exit(1)
    return cs


def update_ABS_program(file_name,param):
    with open(file_name,"r") as f:
        lines = f.readlines()
    changed = False
    for i in range(len(lines)):
        m = re.match("def\s*(Int|Rat)\s*([a-zA-Z0-9_]*).*=.*",lines[i])
        if m is not None:
            if m.group(2) in param:
                logging.debug("Changed parameter {} to {}".format(m.group(2), param[m.group(2)]))
                lines[i] = "def {} {}() = {};\n".format(m.group(1), m.group(2), param[m.group(2)])
                changed = True
    if changed:
        file_id, name = tempfile.mkstemp(suffix='.abs')
        os.close(file_id)
        with open(name,'w') as f:
            f.write("".join(lines))
        logging.debug("Program written into {}".format(name))
        return name
    return ""


def evaluate_configuration(cfg):
    """
    cfg: Configuration containing the parameters.
    """
    pid = os.getpid()
    cfg = {k: cfg[k] for k in cfg if cfg[k]}
    logging.debug("Pid {}, Configuration: {}".format(pid, cfg))

    # test evaluation function
    #return -sum(cfg.values())

    try:

        temp_files = []
        abs_files = []
        for i in ABS_FILES:
            f = update_ABS_program(i, cfg)
            if f:
                temp_files.append(f)
                abs_files.append(f)
            else:
                abs_files.append(i)

        logging.debug("Pid {}, Updated {} files".format(pid, len(temp_files)))

        for i in range(RESUBMISSION_ATTEMPTS):
            try:
                req_files = []
                for j in abs_files:
                    req_files.append(['abs',open(j,'rb')])
                req_files.append(["log_parser",open(LOG_PARSER_PROGRAM,'rb')])

                # to use only one processor for the erlang simulation
                # req_files.append(["-s","1"])

                start_time = datetime.datetime.now()
                logging.debug("Pid {}, Sending request to server, attempt {}".format(
                    pid,i+1))
                response = requests.post("{}:{}/process".format(SERVER_URL,SERVER_PORT),
                                         files=req_files,
                                         headers={'host': SERVER_HOST} if SERVER_HOST else {})

                delta = datetime.datetime.now() - start_time
                logging.debug("Pid {}, Received answer with code {}. Time {}".format(
                    pid, response.status_code, delta.total_seconds()))
                # handle error in the answer
                if response.status_code != requests.codes.ok:
                    raise ValueError("Pid {}, Request failed with error text: {}. Time {}".format(
                        pid, response.text, delta.total_seconds()))
                # parse the answer
                value = float(response.text)
                logging.debug("Pid {}, Quality of the solution: {}".format(
                    pid, value))
                return value  # Minimize!
            except ValueError as e:
                logging.error("Pid {}, Error {}".format(pid,e))
            except requests.exceptions.RequestException as e:
                logging.critical("Pid {}, Connection request error {}".format(pid, e))
            except requests.exceptions.ConnectionError as e:
                logging.error("Pid {}, Connection error {}".format(pid, e))
            if i < RESUBMISSION_ATTEMPTS - 1:
                time.sleep(SLEEP_TIME_AFTER_ERROR)
    finally:
        for i in temp_files:
            if os.path.exists(i):
                os.remove(i)


def worker(proc_num, json_data, scenario, queue):

    try:
        logging.debug("Worker {} started".format(proc_num))
        incumbent = None

        # first process tried the default configuration
        if proc_num == 0:
            scenario["initial_incumbent"] = "DEFAULT"
            logging.debug("First worker: start with testing default scenario.")

        logging.debug("Proc {}. Building the configuration space".format(proc_num))
        try:
            scenario["cs"] = build_config_space(json_data)
        except KeyError as e:
            logging.warning("Proc {}. Error in building the scenario: {}".format(proc_num,e))
            return

        logging.debug("Proc {}. Building the SMAC object".format(proc_num))
        smac = SMAC(scenario=Scenario(scenario),
                    rng=numpy.random.RandomState(proc_num),
                    tae_runner=evaluate_configuration,
                    run_id=proc_num)

        logging.debug("Proc {}. Starting the optimization".format(proc_num))
        incumbent = smac.optimize()

        logging.debug("Proc {}. Optimization has ended with incumbent {}".format(proc_num, incumbent))
    finally:
        logging.debug("Proc {}. Adding in queue the incumbent".format(proc_num))
        queue.put(incumbent)


@click.command()
@click.option('--param-file',
              help='JSON file containing the parameter specification',
              type=click.Path(exists=True, file_okay=True, dir_okay=False, writable=False, readable=True,
                              resolve_path=True),
              default="param_spec.json",
              show_default=True)
@click.option('--output-dir',
              help='File where to store the results of the SMAC executions',
              type=click.Path(exists=False, file_okay=False, dir_okay=True, writable=True, readable=True,
                              resolve_path=True),
              #show_default=True
              default=os.path.join(os.getcwd(),datetime.datetime.now().strftime("%Y%m%d%H%M%S") + "_smac_output")
              )
@click.option('--abs-file','-a',
              multiple=True,
              type=click.Path(exists=True, file_okay=True, dir_okay=False, writable=False, readable=True,
                              resolve_path=True),
              help='ABS files to use. First one contains the parameters to set.',
              default=ABS_FILES)
@click.option('--output-log-parser',
              type=click.Path(exists=True, file_okay=True, dir_okay=False, writable=False, readable=True,
                              resolve_path=True),
              show_default=True,
              help='Python program to parse the output of the ABS simulation.',
              default=LOG_PARSER_PROGRAM)
@click.option('--parallel-executions',
              help='How many parallel execution of SMAC are triggered',
              default=1,
              show_default=True)
@click.option('--global-timeout',
              help='How long in seconds the SMAC3 has to run',
              default=3600*24,
              show_default=True)
@click.option('--simulation-timeout',
              help='How long SMAC is allowed to wait for a single simulation',
              default=3600,
              show_default=True)
@click.option('--global-simulation-limit',
              help='Limit of the number of simulation that SMAC is allowed to do',
              default=100,
              show_default=True)
@click.option('--server-url',
              help='Server URL address',
              show_default=True,
              default=SERVER_URL)
@click.option('--server-port',
              help='Server IP port',
              show_default=True,
              default=SERVER_PORT)
@click.option('--server-host',
              help='Custom header host if needed',
              show_default=True,
              default=SERVER_HOST)

def run(param_file,
        abs_file,
        output_log_parser,
        parallel_executions,
        output_dir,
        global_timeout,
        simulation_timeout,
        global_simulation_limit,
        server_url,
        server_port,
        server_host,
        ):
    """
    Run SMAC on the given scenario
    """

    if not os.path.isdir(output_dir):
        logging.info("Creating the directory {} to store the results".format(output_dir))
        os.makedirs(output_dir)

    scenario = DEFAULT_SCENARIO
    scenario["input_psmac_dirs"] = os.path.join(output_dir, "*")
    scenario["output_dir"] = output_dir
    scenario["wallclock_limit"] = global_timeout
    scenario["cutoff_time"] = simulation_timeout
    scenario["runcount-limit"] = global_simulation_limit

    # needed to call the evaluation function without passing other parameters
    global ABS_FILES, LOG_PARSER_PROGRAM, SERVER_URL, SERVER_PORT, SERVER_HOST

    ABS_FILES = abs_file
    LOG_PARSER_PROGRAM = output_log_parser
    SERVER_URL = server_url
    SERVER_PORT = server_port
    SERVER_HOST = server_host

    logging.info("Parsing JSON file")
    try:
        json_data = json.load(open(param_file))
    except ValueError as e:
        logging.critical("Json file {} is not a valid JSON. Error: {}".format(param_file, e))
        sys.exit(1)

    procs = []
    queue = multiprocessing.Queue()
    for i in range(parallel_executions):
        p = multiprocessing.Process(target=worker, args=(i, json_data, scenario, queue))
        logging.debug("Starting process {}".format(i))
        p.start()
        procs.append(p)

    logging.debug("All process started")

    results = []
    for i in range(parallel_executions):
        logging.debug("Waiting for ending of process {}".format(i))
        results.append(queue.get())

    logging.debug("All incumbents: {}".format(results))

    dirs = [os.path.join(scenario["output_dir"], f) for f in os.listdir(scenario["output_dir"])
            if os.path.isdir(os.path.join(scenario["output_dir"], f))]
    files = [os.path.join(dir, f) for dir in dirs for f in os.listdir(dir)
             if f == "traj_aclib2.json" and os.path.isfile(os.path.join(dir, f))]

    # worst value for the metric based on SMAC3 default
    best_cost = 2147483647
    best_incumbent = None
    wall_clock_time = None
    best_run = None
    for file_name in files:
        with open(file_name) as f:
            lines = f.readlines()
        if lines:
            data = json.loads(lines[-1])
            if data["cost"] < best_cost:
                best_cost = data["cost"]
                best_incumbent = data["incumbent"]
                wall_clock_time = data["wallclock_time"]
                best_run = file_name

    print("Best configuration has cost {}, found after {}, run file {}, with settings {}".format(
        best_cost, wall_clock_time, best_run, best_incumbent))

    logging.info("Execution terminated")

cli.add_command(run)

if __name__ == '__main__':
    cli()
