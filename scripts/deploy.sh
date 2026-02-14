#!/bin/bash

BASEDIR=$(dirname "$0")
SCRIPT_DIR=$(cd $BASEDIR && pwd)
PROJECT_DIR=$(dirname $SCRIPT_DIR)
BUILD_DIR=${PROJECT_DIR}/build

. ${BUILD_DIR}/buildinfo


cd ${PROJECT_DIR}



echo "GRADLE_USER_HOME=$GRADLE_USER_HOME"
ls -al "$GRADLE_USER_HOME" || true

${PROJECT_DIR}/gradlew publish --info --stacktrace \
    -PrepositoryName=${REPOSITORY} \
    -PprojectVersion=${VERSION}
