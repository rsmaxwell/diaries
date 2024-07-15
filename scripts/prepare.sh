#!/bin/bash

BASEDIR=$(dirname "$0")
SCRIPT_DIR=$(cd $BASEDIR && pwd)
PROJECT_DIR=$(dirname $SCRIPT_DIR)
BUILD_DIR=$(PROJECT_DIR)/build


#
# Generate the version and repository depending on how we were called
#
if [ -z "${BUILD_ID}" ]; then
    BUILD_ID="(none)"
    VERSION="0.0.1-SNAPSHOT"
    REPOSITORY=snapshots
else
    VERSION="0.0.1.$((${BUILD_ID}))"
    REPOSITORY=releases
fi

mkdir -p ${BUILD_DIR}
cat > ${BUILD_DIR}/buildinfo <<EOL
REPOSITORY="${REPOSITORY}"
VERSION="${VERSION}"
EOL




#
# Replace tags in the source with build info
#

function ReplaceTags()
{
    SOURCE_DIR=$1
    cd ${SOURCE_DIR}
    find . -name BuildInfo.java | while read filename; do
        echo "Updating ${filename}"
        originalfile=${SOURCE_DIR}/${filename}
        tmpfile=$(mktemp)
        cp --attributes-only --preserve ${originalfile} ${tmpfile}
        cat ${originalfile} | envsubst > ${tmpfile}
        mv ${tmpfile} ${originalfile}
    done
}

export BUILD_ID
export VERSION
export TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"
export GIT_COMMIT="${GIT_COMMIT:-(none)}"
export GIT_BRANCH="${GIT_BRANCH:-(none)}"
export GIT_URL="${GIT_URL:-(none)}"

tags='$VERSION,$BUILD_ID,$TIMESTAMP,$GIT_COMMIT,$GIT_BRANCH,$GIT_URL'

ReplaceTags ${PROJECT_DIR}/diaries-request/src
ReplaceTags ${PROJECT_DIR}/diaries-response/src






