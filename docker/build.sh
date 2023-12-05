#!/bin/bash

set -e

MYDEV=${DEBUG:-0}
MYTYPE=${1:-psf}
PY_VER=${2:-3.10.13-bookworm}
PVER=${PY_VER%%-*}
BASE_TAG="integrations_base_${MYTYPE}_${PVER}"
FINAL_TAG="jupyter_integrations_${MYTYPE}_${PVER}"

WORK_DIR=`mktemp -d`
cleanup() {
  rm -rf "$WORK_DIR"
  echo "Deleted temp working directory: $WORK_DIR."
}

trap "exit 1" hup int pipe quit term
trap cleanup exit

# Fails with alias'd podman. Use symlink instead.
[[ "$(command -pv docker)" ]] || { echo "docker is not installed" 1>&2 ; exit 1; }

### I have no idea what this block does...
### Probably should do this in $WORK_DIR to be idempotent
#if [ ${MYDEV} -eq "1" ]; then
#    CURPWD=`pwd`
#    cd ..
#    cd ..
#    tar zcf /tmp/jup_int.tgz jupyter_integration_base
#    cd ${CURPWD}
#    mv /tmp/jup_int.tgz ./
#    tar zxf jup_int.tgz
#
#    echo "DEV VERSION"
#    MYJUPDOCK="${MYJUPDOCK}_dev"
#    echo "Jupyter Dockerfile: ${MYJUPDOCK}"
#else
#    echo "NON DEV"
#fi
###

echo "MYTYPE: $MYTYPE"
echo "PVER: $PVER"
echo "BASE_TAG: $BASE_TAG"
echo "FINAL_TAG: $FINAL_TAG"

docker_build(){
    local TAG=$1
    local PY_VER=${2:-$PY_VER}
    local TARGET=${3:-""}
    local CACHE_FLG=""

    # When it DEV use cache for sanity
    if [[ $MYDEV -ne 0 ]]; then
        CACHE_FLG="--no-cache"
    fi
    
    docker build $CACHE_FLG \
        --build-arg="PY_VER=$PY_VER" \
        -t ${TAG} .

    if [ $? -eq 0 ]; then
        echo "Successfully completed Docker build for $TAG"
    else
        echo "Build for $TAG failed - exiting"
        exit 1
    fi
}

docker_build ${FINAL_TAG}

if [ $? -eq 0 ]; then
    echo "Final Build Complete"
else
    echo "Final Build for $MYTYPE $PVER failed - exiting"
    exit 1
fi