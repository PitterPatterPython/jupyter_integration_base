#!/bin/bash


MYDEV="0"
MYJUPDOCK="Dockerfile_jupyter_integrations"
MYTYPE="$1"
PVER="$2"

if [ -z ${MYTYPE} ]; then
    echo "No Type selected, defaulting to psf"
    MYTYPE="psf"
fi

if [ -z ${PVER} ]; then
    echo "No Python version provided, defaulting to 310 (3.10)"
    PVER="310"
fi

MYDFILE="Dockerfile_${MYTYPE}_${PVER}"

REQFILE="requirements_${PVER}.txt"

#REQFILE="20230829_requirements_39.txt"



if [ -f ./${MYDFILE} ]; then
    echo "Found Dockerfile for $MYTYPE - Continuing"
else
    echo "Type $MYTYPE does not have an associated dockerfile"
    exit 1
fi

if [ -f ./${REQFILE} ]; then
    echo "Found Requirements file for ${PVER} - Continuing"
else
    echo "Requirements file for ${PVER} (${REQFILE}) not found - exiting"
    exit 1
fi

cp ${REQFILE} ./requirements.txt



if [ ${MYDEV} -eq "1" ]; then
    CURPWD=`pwd`
    cd ..
    cd ..
    tar zcf /tmp/jup_int.tgz jupyter_integration_base
    cd ${CURPWD}
    mv /tmp/jup_int.tgz ./
    tar zxf jup_int.tgz

    echo "DEV VERSION"
    MYJUPDOCK="${MYJUPDOCK}_dev"
    echo "Jupyter Dockerfile: ${MYJUPDOCK}"
else
    echo "NON DEV"
fi


FULL_VERSION=`grep JIVERSION ${MYDFILE} |sed  "s/ENV JIVERSION=//"`

VERSION=`echo -n ${FULL_VERSION}|sed "s/${MYTYPE}//"`
BASE_TAG="integrations_base_${MYTYPE}_${PVER}:$VERSION"

FINAL_TAG="jupyter_integrations_${MYTYPE}_${PVER}:$VERSION"


echo "MYTYPE: $MYTYPE"
echo "PVER: $PVER"
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
    echo "Base build for $MYTYPE - $PVER failed - exiting"
    exit 1
fi



sed "s/~~SRCIMAGE~~/${BASE_TAG}/" ${MYJUPDOCK} > Dockerfile1

if [ "${MYTYPE}" == "stacks" ]; then
    sed "s/RUN \/root\/startup_files\.sh//" Dockerfile1 > Dockerfile
    rm  Dockerfile1
else
    mv Dockerfile1 Dockerfile
fi


docker build -t ${FINAL_TAG} .

if [ $? -eq 0 ]; then
    echo "Final Build Complete"
    docker tag ${FINAL_TAG} jupyter_integrations_${MYTYPE}_${PVER}:latest
    rm ./Dockerfile
else
    echo "Final Build for $MYTYPE $PVER failed - exiting"
    exit 1
fi

rm -rf ./jupyter_integration_base
rm jup_int.tgz
