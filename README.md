# ABS Parameter Optimizer

This tool, called ABS Parameter OPTimizer (ABS POPT) allows the optimization of the parameters of a
model written in ABS.

The basic idea is to run the simulation of the ABS model changing its
parameters and trying to figure out what is the best combination of parameter
based on the output of the model and a metric to optimize.

To understand what are the best parameters, instead of doing a grid search that
could result in an explosion of the number of simulations to be run, we use the
configurator optimizer [SMAC](https://github.com/automl/SMAC3).

Differently from the previous version of the tool that was exploiting the SMAC2 version,
now ABS POPT uses SMAC3 and distributes the simulation works via HTTP POST requests (the
previous version was perfroming the computation on the same machine).

## Tool installation

The tool can be easily install by using by using the
[Docker](https://www.docker.com/) container technology.  Docker supports a
huge variety of OS. In the following we assume that it is correctly installed
on a Linux OS (a similar procedure can be used to install the tool on a
Windows or MacOS). For more information related to Docker and how to use it we invite the reader
to the documentation at [https://www.docker.com/](https://www.docker.com/).


### Deploy the simulation microservices

ABS POPT delegates the task of performing the ABS simulations to microservices, dubbed WORKERS, via
HTTP POST request. The WORKER microservice can be deployed locally by using Docker running the following
commands.

```
sudo docker pull jacopomauro/abs_optimizer:latest
sudo docker run -d -p <PORT>:9001 --name worker_container jacopomauro/abs_optimizer:latest
```

where `<PORT>` is the port used to use the functionalities of the service.

To check if the microservice is succesfully deploy it is possible to send the following 
HTTP request.

```
curl http://localhost:<PORT>/health
```

If the microservice is working you will obtain in return the message `OK`.

### Deploy ABS POPT

ABS POPT can be deployed by using Docker running the following commands.

```
sudo docker pull jacopomauro/abs_optimizer:main
sudo docker run --net="host" -d --name controller_container jacopomauro/abs_optimizer:main \
  /bin/bash -c "while true; do sleep 60; done"
```

## Tool usage

Assuming that the one of more WORKER services (a load balancer can be used to exploit more
instances of WORKER services) are reachable at the url `URL`, port `PORT`, hostname `HOST`,
the first operation to run ABS POPT is to get access to the shell of the ABS POPT container by
running:

```
sudo docker exec -i -t controller_container bash
```

The ABS POPT python program `abs_opt.py` is available in the current folder.

ABS POPT to be run requires
* one of more ABS file to run
* one python program to parse the
  output of the ABS simulation and compute the quality of the simulation (for more details please see below)
* one file defining the parameters to optimize (for more details on the structure of this file please see below).

As an example, ABS POPT comes with a simple ABS program requiring the compilation of one file, viz.
`examples/new_years_eve/NewYearsEve.abs`, the parsing python program
`examples/new_years_eve/solution_quality.py` and the parameter specification file
`examples/new_years_eve/param_spec.json`. The program runs forever and have to be executed with the
option `-l` to interrupt it.
We will use these files to show a simple usage of ABS POPT.

First of all to understand the settings of ABS POPT please run the following command:
```
python abs_opt.py run --help
```

ABS POPT allows to tune different parameters.
To run the ABS POPT requiring at most 5 simulations or running for at most 1 hour, it is possible to run
the following command.

```
python abs_opt.py run \
 --param-file examples/new_years_eve/param_spec.json \
 --abs-file examples/new_years_eve/NewYearsEve.abs \
 --output-log-parser examples/new_years_eve/solution_quality.py \
 --global-simulation-limit 5 \
 --global-timeout 3600
 --abs-option-l 310 
```

This starts the execution of SMAC3 and presents in output the best result obtained.
The simulations of ABS are run with the option "-l" set to 310.

Please note that custom abs programs and files need to be 
copied in the container (e.g., by using `scp` or the volume
sharing capabilities of Docker).
For instance, assuming that the path where the files are stored in `PATH` then 
the ABS POPT container can be started with the following command.

```
sudo docker run --net="host" -v PATH:/files_directory -d --name controller_container jacopomauro/abs_optimizer:main \
  /bin/bash -c "while true; do sleep 60; done"
```

The files will be available inside the container in the directory `/files_directory`.

### Defining the ABS model and the parameters

We assume the existence of an ABS model. This model exposes parameters
that can be tuned. Since ABS main execution does not support the setting
of external parameters, for ABS POPT the ABS code need to contained for all
parameters named `p` a unique line as follows.

```
def Int p() = 0;
```

### Defining the metric

ABS POPT tries to find out the best parameters maximizing the quality of
a simulation.  It is vital therefore to provide a function that associates
the output of a simulation with its quality.  This function is defined by
means of a python program.

The python program has to take a textual file containing the output of the 
ABS simulation and print a number representing the quality of the solution.
ABS POPT tries to minimize this number (i.e., the smaller the number, the
better is the quality of the simulation).

In case of errors due to the model execution, the program can notify that by
exiting with a status that is different than 0. This will be interpreted as
an erroneous simulation.

### Defining the range of the parameters

ABS POPT automatically selects possible domain values for the parameters but
requires to understand what are the parameter considered and what are their
possible ranges. The parameters are defined in a JSON file.

The JSON has a property called `"parameters"` that defines the parameters.
Every parameter has a name, a type, possible values, and a default value.
Types can be `"integer"` or `"ordinal"` to represent an interval of integers
or a set of integers.

As an example in the following we are defining a parameter `p1` that can take
values in the interval `1..10` (default value 1) and a parameter `p2` that can take values in the set
`{4,6,7}` (default value 5).

```
{  
	"parameters":{  
      "p1":{  
         "type":"integer",
         "values":[ 1,10 ]
         ],
         "default":1
      },
      "p2":{  
         "type":"ordinal",
         "values":[ 4,5,7 ]  
         ],
         "default":5
      }
    }
}
```

Note that default values are only used as values to try the first simulation.
 
## Running SMAC3 in parallel

It is possible to run ABS POPT triggering parallel executions of SMAC.
This can be done by simply setting the parameter `--parallel-executions`
to the desired number of parallel runs.

Note that we recommend to have one worker for every execution of SMAC.
To do so it is possible to deploy different workers and then use a load
balancer to distribute the requests.

If a [Kubernetes](https://kubernetes.io/) is available, ABS POPT provides the scripts to set up the
possibility to deploy multiple WORKER services coordinated by an 
[HaProxy load balancer](https://github.com/jcmoraisjr/haproxy-ingress).
Assuming the the user can run the `kubectl` to configure the cluster,
the script to run is `kubernetes/deploy.sh`.
This will create the load balancer with one instance of WORKER in the namespace
`myapp-namespace`. To scale out it is possible to run the following command.

```
kubectl scale deployment http-myapp --replicas=NUM
``` 
 
where N is the desired number of instanes of WORKER (NUM must be less than the number of nodes - 1).
The kubernetes cluster will expose a service called `haproxy-ingress` on a given port.
To find out which port it is please run the command

```
kubectl --namespace=myapp-namespace get services | grep haproxy-ingress
```

Then, assuming that IP is one of the IP nodes of the cluster, PORT is the port to reach
the service deployed on Kubernetes, it is possible to use this
cluster to run the simulations by invoking ABS POPT as follows.

```
python abs_opt.py run \
 --param-file ... \
 --abs-file ... \
 --output-log-parser ... \
 --parallel-executions NUM \
 --global-simulation-limit ... \
 --server-url http://IP \
 --server-port PORT \
 --server-host myapp
```

### Cleaning

To clean up the Docker installation, the following commands can be used.

```
sudo docker stop controller_container && sudo docker rm controller_container
sudo docker stop worker_container && sudo docker rm worker_container
sudo docker rmi jacopomauro/abs_optimizer:latest
sudo docker rmi jacopomauro/abs_optimizer:latest
```