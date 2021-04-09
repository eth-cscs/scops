#!/bin/bash

WDIR="/scratch/snx3000/maximem/scops_msa/deployment/slurm"
TIME="24:00:00"

ci=("pt_eth" "pt_mr" "pa_pr" "pa_rest" "pt_em" "pa_ul" "pt_usi" "ce_ich" "ce_uzh")
port=44500
OPTIONS="-A csstaff -C mc -N 1"
for ci_names in "${ci[@]}"; do

    log_name="log_scops_$(echo ${ci_names} | tr -s ';' '_')-%j"
    srun -t "${TIME}" $OPTIONS -o "${log_name}.out" -e "${log_name}.err" $WDIR/./start_ci.sh "$ci_names" "$port" &
    sleep 3

    port=$(( $port +100 ))
done

