#!/bin/sh

BASEDIR=$(dirname "$0")
SCRIPT_DIR=$(cd $BASEDIR && pwd)
SUBPROJECT_DIR=$(dirname $SCRIPT_DIR)
PROJECT_DIR=$(dirname $SUBPROJECT_DIR)
BUILD_DIR=${SUBPROJECT_DIR}/build

pwd
ls -al 
tree ${PROJECT_DIR}

${PROJECT_DIR}/diaries-request/scripts/prepare.sh
${PROJECT_DIR}/diaries-response/scripts/prepare.sh
