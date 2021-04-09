#!/bin/bash

WDIR="/scratch/snx3000/maximem/scops_msa/deployment/slurm"
TIME="24:00:00"

PORT=12000

LOG_NAME="log_scops_msa-%j"
OPTIONS="-A csstaff -C mc -N 1"
srun -t "${TIME}" -o "${LOG_NAME}.out" -e "${LOG_NAME}.err" $OPTIONS $WDIR/./start_msa.sh "$PORT" &

