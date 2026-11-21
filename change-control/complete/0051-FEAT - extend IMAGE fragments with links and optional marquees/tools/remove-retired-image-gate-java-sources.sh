#!/usr/bin/env bash
# One-off 0051 Step 5 overlay completion (Windows Cygwin, from Diaries parent root).
# Remove ONLY the obsolete gate classes and renamed gate-specific test.
set -euo pipefail

test -f diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/config/ImageAuthoringConfigTest.java
for spec in \
    'diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/utilities/ImageFragmentWritePolicy.java:ImageFragmentWritePolicy' \
    'diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/utilities/ImageFragmentExtensionsWritePolicy.java:ImageFragmentExtensionsWritePolicy' \
    'diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/config/ImageFragmentGateConfigTest.java:ImageFragmentGateConfigTest'
do
    file=${spec%%:*}
    marker=${spec#*:}
    if test -f "$file"; then
        grep -q "$marker" "$file"
        rm -- "$file"
        echo "PASS: removed retired source $file"
    else
        echo "PASS: already absent $file"
    fi
done
