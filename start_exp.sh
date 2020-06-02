#!/bin/bash

rm log/*_output.log

NPERNODE=$1
NNODES=$SLURM_NNODES
WDIR="/scratch/maximem/scops"

ci=("CE_ich" "CE_uzh" "CI" "PA_pr" "PA_rest" "PA_ul" "PT_em" "PT_eth" "PT_mr" "PT_u")
nodelist=($(hostlist -s ' ' -e $SLURM_NODELIST))
port=44500
nnodes=0
while (( $nnodes < $NNODES )); do
   n=${nodelist[$nnodes]}
   npernode=0
   while (( $npernode < $NPERNODE )); do
      k=${ci[$(( $nnodes * $NPERNODE + $npernode))]}
      echo -n "Starting $k experiment on $n ... "
      ssh $n $WDIR/./start_ci.sh $k ci_${k}_20190303000000_20190309235959.trace "$port"  &> $WDIR/log/${k}_output.log &
      port=$(( $port +10 ))
      sleep 10
      echo " done"
      npernode=$(( $npernode +1 ))
   done
   nnodes=$(( $nnodes +1 ))
done
#sleep 6
#rm ci/*/block
