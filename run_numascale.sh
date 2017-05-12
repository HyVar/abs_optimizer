#!/bin/bash

ulimit -u 221184
export SMAC_MEMORY=2048

for i in {1..100}; do
	echo "Running" $i " instance of smac with seed " $i 
	numactl --cpunodebind=$i --membind=$i smac/smac --scenario-file scenario.txt \
    --initial-incumbent RANDOM \
		--validation false \
		--rungroup test \
		--retry-crashed-count 2 \
		--shared-model-mode true \
		--seed $i > "log_run_smac"$i".log" &
done

wait

