#!/bin/bash

LIST_CI="$1"
REGISTER_LOCATION="0.0.0.0:12000"

DOCKER_COMPOSE_FILE="docker-compose.yml"
PORT="17100"

cat <<EOT > $DOCKER_COMPOSE_FILE
version: '3.4'

networks:
  default:
    external:
      name: test-network

services:
EOT

INI_PORT=$PORT
for k in $LIST_CI; do
    touch ci_test/$k/block
cat <<EOT >> $DOCKER_COMPOSE_FILE
   ${k}:
     image: slurm-replay:\${REPLAY_USER}_slurm-18.08.8
     container_name: ${k}
     user: \${REPLAY_USER}
     command: -w ../data/\${${k}_TRACE} -r \${CLOCK_RATE} -P ${INI_PORT} -s \${START_TIME} -p \${PRESET}
     ports:
        - $(($INI_PORT + 1)):$(($INI_PORT + 1))
     volumes:
         - \${SCOPS_PATH}/test/ci_test/${k}:/\${REPLAY_USER}/data
         - \${SCOPS_PATH}/slurm_helper:/\${REPLAY_USER}/slurmR/slurm_helper
         - \${SCOPS_PATH}/test/ci_test/${k}/\${${k}_TRACE}_etc_passwd:/etc/passwd
         - \${SCOPS_PATH}/test/ci_test/${k}/\${${k}_TRACE}_etc_group:/etc/group

EOT
   INI_PORT=$(( $INI_PORT + 100 ))
done

docker-compose -f $DOCKER_COMPOSE_FILE --env-file docker-compose.env up --remove-orphans -d
sleep 15

INI_PORT=$(($PORT +1))
for k in ${LIST_CI}; do
    #IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' test_${k}_1)
    IP="${k}"
    curl -X POST -k -H "Content-Type: application/json" -H "X-Auth-Token: scops" https://$REGISTER_LOCATION/register/ci/$k/$IP:$INI_PORT
    INI_PORT=$(( $INI_PORT + 100 ))
done
