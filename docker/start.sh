#!/bin/bash

########################
# Edit these for local storage of things to match you home dir

NOTEBOOKDIR="/Users/${USER}/Notebooks"
ENV_FILE="/Users/${USER}/jupyter_integration_data_sources.env"

########################
# Advanced Variables, probably don't need to change these

MYTYPE="conda"
PORT="8888"
IMG="integrations_${MYTYPE}:latest"

########################
# Don't Change below this

ENV_TEMPLATE="./jupyter_integration_data_sources_template.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "Creating $ENV_FILE from template: $ENV_TEMPLATE"
    cp ${ENV_TEMPLATE} ${ENV_FILE}
fi

ID=$(docker run -d -p${PORT}:8888 --env-file=${ENV_FILE} -v $NOTEBOOKDIR:/root/notebooks ${IMG} /root/start_jupyter.sh)

echo "Waiting for Start"
sleep 5

docker logs $ID


