#!/bin/bash

module load sarus

PORT="$1"

WDIR="/scratch/snx3000/maximem/scops_msa/deployment/slurm"
NODE=$(hostname -i)
REGISTER_LOCATION="$NODE:$PORT"
echo "$REGISTER_LOCATION" > "$WDIR/register.conf"


SCENARIO="scenario1"
DATA_PATH="/scratch/snx3000/maximem/scops_msa/log/deployment/msa"
DATA_EXEC="/scratch/snx3000/maximem/scops_msa/msa_services"
CI_PATH="/scratch/snx3000/maximem/scops_msa/${SCENARIO}/ci_config"
CI_NAMES=$(for x in $(ls -1 $CI_PATH); do echo "${x%%.*},"; done | tr -d '\n')

rm -f "${DATA_PATH}/*.log" "${DATA_PATH}/*.pickle"
sarus run \
    --mount=type=bind,source="${DATA_PATH}",destination="/data" \
    --mount=type=bind,source="${DATA_EXEC}",destination="/exec" \
    --mount=type=bind,source="${CI_PATH}",destination="/ci_config" \
    load/mmxcscs/scops_msa_debug:latest ${NODE} ${PORT} ${REGISTER_LOCATION} ${CI_NAMES::-1}
