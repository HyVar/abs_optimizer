"""
Program that defines the function evaluate that parses the output of the ABS program and returns the metric value (i.e.
a float) to minimize.
"""

import click
import logging
import sys
import traceback

def evaluate(lines):

    scale_in = []
    scale_out = []
    latencies = []
    end = -1

    for line in lines:
        if line.startswith("scale_in"):
            #scale_in,time,component_name
            ls = line.split(",")
            scale_in.append(int(ls[1]))
        elif line.startswith("scale_out"):
            # scale_out,time,component_name
            ls = line.split(",")
            scale_out.append(int(ls[1]))
        elif line.startswith("job"):
            #job,start_time,end_time,latency,...
            ls = line.split(",")
            latencies.append(int(ls[3]))
        elif line.startswith("simulation_ended"):
            #simulation_ended,826
            ls = line.split(",")
            end = int(ls[1])
        elif line.startswith("FATAL"):
            raise ValueError("Simulation was not correct. FATAL found in output")

    if end < 0:
        raise ValueError("Simulation was not ended. simulation_ended not found in output")

    if not latencies:
        raise ValueError("No jobs found in output")

    average_latency = sum(latencies) / len(latencies)

    # process scaling decisions
    vms = {}
    for i in scale_in:
        if i in vms:
            vms[i] += -1
        else:
            vms[i] = -1
    for i in scale_out:
        if i in vms:
            vms[i] += 1
        else:
            vms[i] = 1

    counter = 0
    area = 0
    time = 0
    for i in sorted(vms.keys()):
        area += (i-time) * counter
        counter += vms[i]        
        time = i
    area = (end-time)*counter
    average_vms = area / end

    if average_latency > 300000:
        return average_latency
    else:
        return average_vms*100


@click.command()
@click.argument("input_file",
              type=click.Path(exists=True, file_okay=True, dir_okay=False, writable=False, readable=True,
                              resolve_path=True))
@click.option('--log-level',
              help='Log level',
              type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
              default="ERROR",
              show_default=True)
def main(input_file,log_level):
    logging.basicConfig(format="[%(asctime)s][%(levelname)s][%(name)s]%(message)s",
                        level=log_level)

    with open(input_file,'r') as f:
        lines = f.readlines()
    try:
        print("{}".format(evaluate(lines)))
    except Exception as e:
        traceback.print_exc()
        print("Error: {}".format(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
