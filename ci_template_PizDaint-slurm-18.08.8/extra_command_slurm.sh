#!/bin/bash

# Setup initial number of available nodes

echo -n "extra slurm command... "
scontrol update FrontEnd=localhost state=RESUME Reason="complete slurm replay setup"
#partitions=$(sinfo -o %R --noheader)
#for p in $partitions; do
#    scontrol update PartitionName=$p state=DOWN
#done;
scontrol update PartitionName=normal state=UP

nodes=$(sinfo -o %N --noheader)
scontrol update NodeName=$nodes state=DOWN Reason="complete slurm replay setup"

SCOPS_NODELIST_RESUME="$(cat /$REPLAY_USER/data/node_resume.lst)"
scontrol update NodeName="${SCOPS_NODELIST_RESUME}" state=RESUME Reason="Initial scops setup"
echo "done"
