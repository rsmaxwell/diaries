#!/bin/sh

set -x

BASEDIR=$(dirname "$0")
SCRIPT_DIR=$(cd $BASEDIR && pwd)
SUBPROJECT_DIR=$(dirname $SCRIPT_DIR)
PROJECT_DIR=$(dirname $SUBPROJECT_DIR)
BUILD_DIR=${SUBPROJECT_DIR}/build

pwd
ls -al 
tree

cd ${SUBPROJECT_DIR}


${PROJECT_DIR}/gradlew publish \
    -PrepositoryName=${REPOSITORY} \
    -PprojectVersion=${VERSION}
