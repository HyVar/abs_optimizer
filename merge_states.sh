#!/bin/bash

smac/util/state-merge --directories $1 --scenario-file scenario.txt --outdir $2 --repair-smac-invariant false

CSV_FILE=`ls $2 | grep runs_and_results-it*`

if [ -z $CSV_FILE ]; then
	echo "Best solution" 
	for f in `ls $1/traj-run*`; do
		tail -n -1 $f; done | grep -v ', 1.0E9,' | awk -F "," 'NR == 1 || $2 < min {line = $0; min = $2}END{print line"\n"min"\n";}'

	echo "Positive Runs"
	for f in `ls $1/log-run*`; do cat $f ; done | grep quality: | grep INFO | grep -v 1.0E9 | wc -l

	echo "Crashes"
	for f in `ls $1/log-run*`; do cat $f ; done | grep "CRASHED, 0" | wc -l

else

	BEST=`cat $2/$CSV_FILE | grep SAT | awk -F "," 'NR == 1 || $4 < min {line = $0; min = $4}END{print line}'`
  QUALITY=`echo $BEST"\n" | awk -F "," 'END{print $4;}'`

	echo "Best solution found with quality " $QUALITY
	NUM_SOL=`echo $BEST | awk -F "," 'END{print $2;}'`
	TXT_FILE=`ls $2 | grep paramstrings-it*`
	cat $2/$TXT_FILE | grep "^$NUM_SOL:"

	echo "Positive Runs"
	cat $2/$CSV_FILE | grep SAT | wc -l

	echo "Crashes"
	cat $2/$CSV_FILE | grep CRASH | wc -l

fi


