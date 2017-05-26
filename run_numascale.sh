#!/bin/bash

ulimit -u 221184
export SMAC_MEMORY=2048

PAR_PROC=104

OPT=" --scenario-file scenario.txt"
OPT=$OPT" --initial-incumbent RANDOM"
OPT=$OPT" --validation false"
OPT=$OPT" --shared-model-mode true"
OPT=$OPT" --abort-on-first-run-crash false"

if [ $# -eq 1 ] && [ $1 = "--restore" ]; then
	for ((i=1;i<=$PAR_PROC;i++)); do
		echo "Restoring running" $i " instance of smac with seed " $i
		echo "State directory"  smac-output/test/state-run$i
		numactl --cpunodebind=$i --membind=$i smac/smac $OPT \
			--rungroup test-restore \
			--restore-scenario smac-output/test/state-run$i \
		  --seed $i >> "log_run_smac"$i".log" &
	done
elif [ $# -eq 2 ] && [ $1 = "--warmup" ]; then
	for ((i=1;i<=$PAR_PROC;i++)); do
		echo "Running" $i " instance of smac with seed " $i
		echo "Warmup state directory" $2
		numactl --cpunodebind=$i --membind=$i smac/smac $OPT \
			--rungroup test-warmup \
			--warmstart $2 \
		  --seed $i >> "log_run_smac"$i".log" &
	done
else
	for ((i=1;i<=$PAR_PROC;i++)); do
		echo "Running" $i " instance of smac with seed " $i 
		numactl --cpunodebind=$i --membind=$i smac/smac $OPT \
			--rungroup test \
			--seed $i > "log_run_smac"$i".log" &
	done
fi

wait

