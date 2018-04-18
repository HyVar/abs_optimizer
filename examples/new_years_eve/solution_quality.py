"""
Program that defines the function evaluate that parses the output of the ABS program and returns the metric value (i.e.
a float) to minimize.
"""

import click
import logging
import sys
import traceback

def evaluate(lines):

    for line in lines:
        ls = line.split(",")
        if ls[0] == "req":
            total = int(ls[1])
        elif ls[0] == "succ":
            success = int(ls[1])
        elif ls[0] == "tel_rsc":
            tel_rsc = int(ls[1])
        elif ls[0] == "sms_rsc":
            sms_rsc = int(ls[1])

    successrate = 100*float(success)/total


    # if success rate is greater than 85 then we minimize the resources
    #   sms_rsc + tel_rsc
    # otherwise we maximise the success rate (since sms_rsc + tel_rsc << 1000)
    #   success rate will be always between 0 and 100
    #    1100 - successrate
    if successrate >= 85:
        #print("Quality {}".format(sms_rsc + tel_rsc)) 
        return sms_rsc + tel_rsc
    else:
        #print("Quality {}".format(1100 - successrate )) 
        return 1100 - successrate 


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
