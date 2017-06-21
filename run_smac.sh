#!/bin/bash

# option --restore to restart
# option warmup <dir> to use previous exectution to restart
# dir can be obtained by
# smac/util/state-merge --directories smac-output/test --scenario-file scenario.txt --outdir <dir>

export SMAC_MEMORY=2048

PAR_PROC=1

OPT="--scenario-file scenario.txt"
OPT=$OPT" --initial-incumbent RANDOM"
OPT=$OPT" --validation false"
OPT=$OPT" --shared-model-mode true"
OPT=$OPT" --abort-on-first-run-crash false"

#		--retry-crashed-count 2 \

if [ $# -eq 1 ] && [ $1 = "--restore" ]; then
	for ((i=1;i<=$PAR_PROC;i++)); do
		echo "Restoring running" $i " instance of smac with seed " $i
		echo "State directory"  smac-output/test/state-run$i
		smac/smac $OPT \
			--rungroup test-restore \
			--restore-scenario smac-output/test/state-run$i \
		  --seed $i >> "log_run_smac"$i".log" &
	done
elif [ $# -eq 2 ] && [ $1 = "--warmup" ]; then
	for ((i=1;i<=$PAR_PROC;i++)); do
		echo "Running" $i " instance of smac with seed " $i
		echo "Warmup state directory" $2
		smac/smac $OPT \
			--rungroup test-warmup \
			--warmstart $2 \
		  --seed $i >> "log_run_smac"$i".log" &
	done
else
	for ((i=1;i<=$PAR_PROC;i++)); do
		echo "Running" $i " instance of smac with seed " $i 
		smac/smac $OPT \
			--rungroup test \
			--seed $i > "log_run_smac"$i".log" &
	done
fi

wait
