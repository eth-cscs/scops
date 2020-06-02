#!/bin/bash

module load sarus

CI="$1"
TRACE=$(basename "$2")
PORT="$3"
CLOCK_RATE="0.06"
START_TIME=1551567600
PRESET="0,0,0,0"

if [ -x "$(command -v sarus)" ]; then
REPLAY_USER=maximem
DATA_PATH="/scratch/maximem/scops"
export DISTIME_SHMEMCLOCK_NAME="/Shmem_${CI}"
export MAX_SERVER_THREADS=8
set -x
sarus run \
    --mount=type=bind,source="${DATA_PATH}/ci/$CI",destination="/${REPLAY_USER}/data" \
    --mount=type=bind,source="${DATA_PATH}/slurm_helper",destination="/${REPLAY_USER}/slurmR/slurm_helper" \
    load/mmxcscs/slurm-replay:${REPLAY_USER}_slurm-18.08.8 ./start_replay.sh -w ../data/${TRACE} -r $CLOCK_RATE -P $PORT -s "${START_TIME}" -p "${PRESET}"
else
REPLAY_USER=replayuser
DATA_PATH="/Users/maximem/dev/docker/scops"
set -x
docker run --rm -it \
    --volume ${DATA_PATH}/ci/$CI:/${REPLAY_USER}/data \
    --volume ${DATA_PATH}/slurm_helper:/${REPLAY_USER}/slurmR/slurm_helper \
    --volume ${DATA_PATH}/ci/$CI/${TRACE}_etc_passwd:/etc/passwd \
    --volume ${DATA_PATH}/ci/$CI/${TRACE}_etc_group:/etc/group \
    -h localhost mmxcscs/slurm-replay:${REPLAY_USER}_slurm-18.08.8
fi
