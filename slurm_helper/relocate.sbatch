#!/bin/bash

NAME="$1"
export PATH="/$REPLAY_USER/data/slurm_helper":$PATH
cmd="rsvmgt $NAME + ${SLURM_NODELIST}"

echo "$cmd"
eval "$cmd"

sleep 10
