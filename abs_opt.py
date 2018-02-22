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
import itertools
from functools import partial

# Import ConfigSpace and different types of parameters
from smac.configspace import ConfigurationSpace
from ConfigSpace.hyperparameters import CategoricalHyperparameter, \
    OrdinalHyperparameter, UniformIntegerHyperparameter
from ConfigSpace.conditions import InCondition

# Import SMAC-utilities
from smac.tae.execute_func import ExecuteTAFuncDict
from smac.scenario.scenario import Scenario
from smac.facade.smac_facade import SMAC

DEFAULT_SCENARIO = {"wallclock_limit": 60,#3600*24,
                    "cutoff_time": 1800,
                    "runcount-limit": 100,
                    "run_obj": "quality",
                    "deterministic": "true",
                    "shared_model": "true",
                    "initial_incumbent": "RANDOM",
                    "abort_on_first_run_crash": "True",
                    }


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

    for i in data["parameters"]:
        obj = data["parameters"][i]
        if obj["type"] == "integer":
            if min(obj["values"]) < max(obj["values"]):
                cs.add_hyperparameter(UniformIntegerHyperparameter(
                    i, min(obj["values"]), max(obj["values"]), default_value=obj["default"]))
            else:
                logging.warning("Parameter {} can take only one value. It will be ignored".format(i))
        elif obj["type"] == "ordinal":
            if len(obj["values"]) > 1:
                cs.add_hyperparameter(OrdinalHyperparameter(
                    i, obj["values"], default_value=obj["default"]))
            else:
                logging.warning("Parameter {} can take only one value. It will be ignored".format(i))
        else:
            logging.critical("Parameter type {} for parameter {} not supported. Exiting".format(obj["type"],i))
            sys.exit(1)
    return cs

    # kernel = CategoricalHyperparameter("kernel", ["linear", "rbf", "poly", "sigmoid"], default_value="poly")
    # cs.add_hyperparameter(kernel)
    # C = UniformFloatHyperparameter("C", 0.001, 1000.0, default_value=1.0)
    # shrinking = CategoricalHyperparameter("shrinking", ["true", "false"], default_value="true")
    # cs.add_hyperparameters([C, shrinking])
    #
    # # Others are kernel-specific, so we can add conditions to limit the searchspace
    # degree = UniformIntegerHyperparameter("degree", 1, 5, default_value=3)  # Only used by kernel poly
    # coef0 = UniformFloatHyperparameter("coef0", 0.0, 10.0, default_value=0.0)  # poly, sigmoid
    # cs.add_hyperparameters([degree, coef0])
    # use_degree = InCondition(child=degree, parent=kernel, values=["poly"])
    # use_coef0 = InCondition(child=coef0, parent=kernel, values=["poly", "sigmoid"])
    # cs.add_conditions([use_degree, use_coef0])


def evaluate_configuration(cfg):
    """
    cfg: Configuration containing the parameters.
    """
    cfg = {k: cfg[k] for k in cfg if cfg[k]}
    print("Config {}".format(cfg))

    metric = 0
    for k in cfg:
        metric += pow(cfg[k],2)

    return -metric  # Minimize!


def worker(proc_num, json_data, scenario, queue):

    # first process tried the default configuration
    if proc_num == 0:
        scenario["initial_incumbent"] = "DEFAULT"

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
    queue.put(incumbent)

    #inc_value = evaluate_configuration(incumbent)


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
              default=os.path.join(os.getcwd(),datetime.datetime.now().strftime("%Y%m%d%H%M%S") + "_smac_output"),
              show_default=True)
@click.option('--abs_file',
              multiple=True,
              type=click.Path(exists=True, file_okay=True, dir_okay=False, writable=False, readable=True,
                              resolve_path=True),
              help='ABS files to use',
              default=[])
@click.option('--parallel-executions',
              help='How many parallel execution of SMAC are triggered',
              default=1,
              show_default=True)
def run(param_file,
        abs_file,
        parallel_executions,
        output_dir
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

    logging.info("Parsing JSON file")
    try:
        json_data = json.load(open(param_file))
    except ValueError as e:
        logging.critical("Json file {} is not a valid JSON. Error: {}".format(param_file, e))
        sys.exit(1)



    #worker_plus = partial(worker, json_data=json_data, scenario=scenario)

    procs = []
    queue = multiprocessing.Queue()
    for i in range(parallel_executions):
        p = multiprocessing.Process(target=worker, args=(i, json_data, scenario, queue))
        p.start()
        procs.append(p)

    results = []
    for i in procs:
        i.join()
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
