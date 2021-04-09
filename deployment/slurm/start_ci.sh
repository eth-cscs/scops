#!/bin/bash

module load sarus

CI_STR="$1"
PORT="$2"
NODE=$(hostname -i)

WDIR="/scratch/snx3000/maximem/scops_msa/deployment/slurm"
REGISTRY_LOCATION=$(cat "$WDIR/register.conf")

CLOCK_RATE="0.06"
START_TIME="1551567600"
PRESET="0,0,0,0"
REPLAY_USER="maximem"

SCENARIO="scenario1"
DATA_PATH="/scratch/snx3000/maximem/scops_msa"
SCENARIO_PATH="/scratch/snx3000/maximem/scops_msa/${SCENARIO}"
LDIR="/scratch/snx3000/maximem/scops_msa/log/deployment/ci"

export MAX_SERVER_THREADS=8

IFS=";" read -r -a ci_n <<< "${CI_STR}"
for ci_name in "${ci_n[@]}"; do
    rm -f "$LDIR/*${ci_name}*.log"
    echo -n "Deploying $ci_name on $NODE ... "
    CI_PATH="${SCENARIO_PATH}/ci_data/${ci_name}"
    TRACE=$(basename $(grep "trace" "${SCENARIO_PATH}/ci_config/${ci_name}.json" | cut -d ':' -f2 | tr -d '", '))
    export DISTIME_SHMEMCLOCK_NAME="/Shmem_${ci_name}"
    touch "$CI_PATH/block"
    sarus run \
        --mount=type=bind,source="${CI_PATH}",destination="/${REPLAY_USER}/data" \
        --mount=type=bind,source="${DATA_PATH}/slurm_helper",destination="/${REPLAY_USER}/slurmR/slurm_helper" \
        load/mmxcscs/slurm-replay:${REPLAY_USER}_slurm-18.08.8 -w ../data/${TRACE} -r $CLOCK_RATE -P $PORT -s "${START_TIME}" -p "${PRESET}" &> "$LDIR/${ci_name}.log" &
    sleep 15

    curl -X POST -k -H "Content-Type: application/json" -H "X-Auth-Token: scops" https://${REGISTRY_LOCATION}/register/ci/$ci_name/$NODE:$(($PORT+1)) &> "$LDIR/curl_${ci_name}.out"
    PORT=$(( $PORT +10 ))
    echo " done"
done

sleep $(( 24 *3600 ))
