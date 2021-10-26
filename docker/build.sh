#!/bin/bash

MYTYPE="$1"

MYDFILE="Dockerfile_${MYTYPE}"



if [ -f ./${MYDFILE} ]; then
    echo "Found Dockerfile for $MYTYPE - Continuing"
else
    echo "Type $MYTYPE does not have an associated dockerfile"
    exit 1
fi

FULL_VERSION=`grep JIVERSION ${MYDFILE} |sed  "s/ENV JIVERSION=//"`

VERSION=`echo -n ${FULL_VERSION}|sed "s/${MYTYPE}_//"`
BASE_TAG="integrations_base_${MYTYPE}:$VERSION"

FINAL_TAG="jupyter_integrations_${MYTYPE}:$VERSION"


echo "MYTYPE: $MYTYPE"
echo "MYDFILE: $MYDFILE"
echo "FULL_VERSION: $FULL_VERSION"
echo "VERSION: $VERSION"
echo "BASE_TAG: $BASE_TAG"
echo "FINAL_TAG: $FINAL_TAG"

cp $MYDFILE ./Dockerfile

docker build -t ${BASE_TAG} .

if [ $? -eq 0 ]; then
    echo "Complete with base build - Proceeding to Integrations Build"
    rm ./Dockerfile
else
    echo "Base build for $MYTYPE failed - exiting"
    exit 1
fi


sed "s/~~SRCIMAGE~~/${BASE_TAG}/" Dockerfile_jupyter_integrations > Dockerfile1

if [ "${MYTYPE}" == "stacks" ]; then
    sed "s/RUN \/root\/startup_files\.sh//" Dockerfile1 > Dockerfile
    rm  Dockerfile1
else
    mv Dockerfile1 Dockerfile
fi


docker build -t ${FINAL_TAG} .

if [ $? -eq 0 ]; then
    echo "Final Build Complete"
    docker tag ${FINAL_TAG} jupyter_integrations_${MYTYPE}:latest
    rm ./Dockerfile
else
    echo "Final Build for $MYTYPE failed - exiting"
    exit 1
fi

