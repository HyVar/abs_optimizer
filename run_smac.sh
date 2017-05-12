#!/bin/bash

# uncomment the following line to check the scenario
#smac/util/verify-scenario --scenarios smac_scenario/scenario.txt --verify-instances false

smac/smac --scenario-file scenario.txt --seed 1 --validation false \
	--rungroup test \
	--retry-crashed-count 2
#  --abort-on-first-run-crash
