#!/bin/bash

# uncomment the following line to check the scenario
#smac/util/verify-scenario --scenarios smac_scenario/scenario.txt --verify-instances false

export SMAC_MEMORY=2048

for i in {1..4}; do
	echo "Running" $i " instance of smac with seed " $i 
	smac/smac --scenario-file scenario.txt \
		--initial-incumbent RANDOM \
		--validation false \
		--rungroup test \
		--retry-crashed-count 2 \
		--shared-model-mode true \
		--seed $i > "log_run_smac"$i".log" &
done

wait
