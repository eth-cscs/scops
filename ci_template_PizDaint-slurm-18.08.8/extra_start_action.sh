#!/bin/bash

BLOCK_FILE="/$REPLAY_USER/data/block"
echo  -n "Extra start action: blocking... "
while [ -f "$BLOCK_FILE" ]; do
    inotifywait -qqt 2 -e delete "$BLOCK_FILE"
done
echo "done."
