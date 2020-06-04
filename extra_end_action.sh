#!/bin/bash

BLOCK_FILE="/$REPLAY_USER/data/block_end"
touch ${BLOCK_FILE}
echo  -n "Blocking... "
while [ -f "$BLOCK_FILE" ]; do
    inotifywait -qqt 2 -e delete "$BLOCK_FILE"
done
date
echo "done"
