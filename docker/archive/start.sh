#!/bin/bash

########################
# Edit these for local storage of things to match you home dir

NOTEBOOKDIR="/Users/${USER}/Notebooks"
ENV_FILE="/Users/${USER}/jupyter_integration_data_sources.env"

########################
# Advanced Variables, probably don't need to change these

MYTYPE="$1"

if [ "${MYTYPE}" == "conda" ]; then
    CMD="/root/start_jupyter.sh"
    DHOME="/root"
elif [ "${MYTYPE}" == "stacks" ]; then
    CMD=""
    DHOME="/home/jovyan"
else
    echo "Must pass stacks or conda to this script"
    exit 1
fi


PORT="8888"
IMG="integrations_${MYTYPE}:latest"

########################
# Don't Change below this

ENV_TEMPLATE="./jupyter_integration_data_sources_template.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "Creating $ENV_FILE from template: $ENV_TEMPLATE"
    cp ${ENV_TEMPLATE} ${ENV_FILE}
fi

docker run -p${PORT}:8888 --env-file=${ENV_FILE} -v $NOTEBOOKDIR:${DHOME}/Notebooks ${IMG} ${CMD}



