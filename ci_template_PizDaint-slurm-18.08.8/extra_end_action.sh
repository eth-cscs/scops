#!/bin/bash

BLOCK_FILE="/$REPLAY_USER/data/block"
touch ${BLOCK_FILE}
echo  -n "Extra end action: blocking... "
while [ -f "$BLOCK_FILE" ]; do
    inotifywait -qqt 2 -e delete "$BLOCK_FILE"
done
date
echo "done."
