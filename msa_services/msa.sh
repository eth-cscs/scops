#!/bin/bash

NODE="$1"
PORT="$2"
REGISTER_LOCATION="$3"
CI_NAMES="$4"

SERVICE_NAME="registry"
echo " --- $SERVICE_NAME --- "
python ./${SERVICE_NAME}_ms.py --port ${PORT} &
sleep 5

SERVICE_NAME="hwstate_mgr"
echo " --- $SERVICE_NAME --- "
PORT=$(( $PORT +10 ))
python ./${SERVICE_NAME}_ms.py --port ${PORT} --registry ${REGISTER_LOCATION} &
sleep 5
curl -X POST -k -H "Content-Type: application/json" -H "X-Auth-Token: scops" https://${REGISTER_LOCATION}/register/msa/$SERVICE_NAME/$NODE:$PORT

SERVICE_NAME="elastic"
echo " --- $SERVICE_NAME --- "
python ./${SERVICE_NAME}_ms.py --registry ${REGISTER_LOCATION} --ci_list ${CI_NAMES}
