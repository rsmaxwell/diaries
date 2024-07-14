#!/bin/sh

BASEDIR=$(dirname "$0")
SCRIPT_DIR=$(cd $BASEDIR && pwd)
SUBPROJECT_DIR=$(dirname $SCRIPT_DIR)
PROJECT_DIR=$(dirname $SUBPROJECT_DIR)
BUILD_DIR=${SUBPROJECT_DIR}/build

${PROJECT_DIR}/project/diaries-request/scripts/deploy.sh
${PROJECT_DIR}/project/diaries-response/scripts/deploy.sh
