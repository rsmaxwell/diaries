#!/bin/sh

set -x 

if [ -z "${BUILD_ID}" ]; then
    BUILD_ID="(none)"
    VERSION="0.0.1-SNAPSHOT"
    REPOSITORY=snapshots
else
    VERSION="0.0.1.$((${BUILD_ID}))"
    REPOSITORY=releases
fi


BASEDIR=$(dirname "$0")
SCRIPT_DIR=$(cd $BASEDIR && pwd)
PROJECT_DIR=$(dirname $SCRIPT_DIR)
BUILD_DIR=${PROJECT_DIR}/build


mkdir -p ${BUILD_DIR}
cd ${BUILD_DIR}

cat > buildinfo <<EOL
VERSION="${VERSION}"
REPOSITORY="${REPOSITORY}"
EOL


${PROJECT_DIR}/mqtt-rpc-example-request/scripts/prepare.sh
${PROJECT_DIR}/mqtt-rpc-example-response/scripts/prepare.sh
