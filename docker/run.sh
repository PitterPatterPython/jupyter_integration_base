#!/bin/bash

########################

source jupyter_integrations.cfg

########

if [ -d "$NOTEBOOKDIR" ]; then
    echo "Notebook directory found"
else
    mkdir $NOTEBOOKDIR
fi

if [ -f "$NOTEBOOKDIR/shared_function_template.py" ]; then
    echo "Shared function template exists"
else
    cp shared_function_template.py ${NOTEBOOKDIR}/
fi



MYTYPE="$1"
PVER="$2"
MYPORT="$3"

if [ -z ${MYTYPE} ]; then
    echo "No Type selected, defaulting to psf"
    MYTYPE="psf"
fi

if [ -z ${PVER} ]; then
    echo "No Python version provided, defaulting to 310 (3.10)"
    PVER="310"
fi


if [ "$MYPORT" == "" ]; then
    echo "No port provided, using port 8888"
    LOCAL_PORT="8888"
else
    echo "Using provided port $MYPORT"
    LOCAL_PORT="$MYPORT"
fi

MYDFILE="Dockerfile_${MYTYPE}_${PVER}"

if [ -f ./${MYDFILE} ]; then
    echo "Found Dockerfile for $MYTYPE - $PVER - Continuing"
    RUN_IMG="jupyter_integrations_${MYTYPE}_${PVER}"
else
    docker image inspect $MYTYPE >  /dev/null
    if [ $? -eq 0 ]; then
        echo "Found Jupyter image: $MYTYPE"
        RUN_IMG="$MYTYPE"
    else
        echo "No image type or actual image named: $MYTYPE"
        exit 1
    fi
fi


echo ""
echo "Using $RUN_IMG for our run image"
echo ""


########################
# Advanced Variables, probably don't need to change these

CONDA_TEST=`echo -n "${RUN_IMG}"|grep conda`
if [ "$CONDA_TEST" != "" ]; then
    echo "Conda Image Found - Using that as our type"
    RUN_TYPE="conda"
    CMD="/root/start_jupyter.sh"
    DHOME="/root"
fi

PSF_TEST=`echo -n "${RUN_IMG}"|grep psf`
if [ "$PSF_TEST" != "" ]; then
    echo "PSF Image Found - Using that as our type"
    RUN_TYPE="psf"
    CMD="/root/start_jupyter.sh"
    DHOME="/root"
fi

STACKS_TEST=`echo -n "${RUN_IMG}"|grep stacks`
if [ "$STACKS_TEST" != "" ]; then
    echo "Stacks Image Found - Using that as our type"
    RUN_TYPE="stacks"
    CMD=""
    DHOME="/home/jovyan"
fi



########################
# Don't Change below this

ENV_TEMPLATE="./jupyter_integration_data_sources_template.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "Creating $ENV_FILE from template: $ENV_TEMPLATE"
    cp ${ENV_TEMPLATE} ${ENV_FILE}
else
    echo "Using Existing $ENV_FILE for Datasources"
fi

echo ""
echo  "Running on port $LOCAL_PORT"
echo ""
echo ""


echo "Also running on port 5678"

#docker run -p${LOCAL_PORT}:8888 -p5678:5678 --env-file=${ENV_FILE} -v $NOTEBOOKDIR:${DHOME}/Notebooks ${RUN_IMG} ${CMD}

# docker network create -d bridge myjupnet

 docker run -p${LOCAL_PORT}:8888 -p5678:5678 --env-file=${ENV_FILE} -v $NOTEBOOKDIR:${DHOME}/Notebooks --net myjupnet ${RUN_IMG} ${CMD}
