#!/bin/bash

rm -f ../../log/deployment/msa/*/*.log
rm -f ../../log/deployment/msa/*/*.pickle

docker-compose up
