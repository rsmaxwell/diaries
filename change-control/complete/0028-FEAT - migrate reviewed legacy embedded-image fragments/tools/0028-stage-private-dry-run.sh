#!/usr/bin/env bash
# Windows PC, Cygwin. Stage only reviewed PRIVATE 0028 migration inputs on pluto.
# Transient runtime stage; no DB or production service mutation. Run after owner-approved
# maintenance readiness, before isolation if possible.
(
  set -euo pipefail
  umask 077
  feature='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
  jar_dir="$feature/evidence/Step 3/private/20261124T151206Z-release-artifact"
  prepared="$feature/evidence/Step 1/private/20261123T144651Z-reviewed-manifest-prepared"
  jar="$jar_dir/diaries-0028-reviewed-migration-fat.jar"
  script="$feature/tools/0028-pluto-production-dry-run.py"
  test -s "$jar" && test -s "$jar_dir/ARTIFACT-IDENTITY.txt" && test -f "$script" || {
    echo 'FAIL: pinned PRIVATE JAR / identity / one-shot script missing' >&2; exit 1;
  }
  grep -Fxq 'source_commit=7aa6296e0c675b3d315e9a46bb0dd70202a8cd55' "$jar_dir/ARTIFACT-IDENTITY.txt" || {
    echo 'FAIL: pinned JAR does not identify the published 0028 responder source' >&2; exit 1;
  }
  hash=$(sha256sum "$jar" | awk '{print $1}')
  grep -Fxq "artifact_sha256=$hash" "$jar_dir/ARTIFACT-IDENTITY.txt" || {
    echo 'FAIL: pinned release digest mismatch' >&2; exit 1;
  }
  for name in 0028-dispositions.csv 0028-image-decisions.csv 0028-v2-preservation-decisions.PRIVATE.csv PREPARATION-RESULT.json SHA256SUMS.txt; do
    test -s "$prepared/$name" || { echo "FAIL: missing manifest input: $name" >&2; exit 1; }
  done
  (cd "$prepared" && sha256sum --check SHA256SUMS.txt) || exit 1
  # /run/user/<uid> is managed by logind and may vanish after SSH logout.
  # Use a root-created, owner-only /run directory which survives SSH sessions
  # but is lost on host reboot. Never place private manifests in the project backup.
  stage='/run/diaries-0028-production-migration-input'
  ssh pluto "test ! -e '$stage' && test ! -L '$stage' && \
    sudo -n install -d -m 700 -o \"\$(id -un)\" -g \"\$(id -gn)\" '$stage' && \
    umask 077 && mkdir -m 700 '$stage/reviewed'" || {
    echo 'FAIL: private /run stage unavailable/exists; no overwrite' >&2; exit 1;
  }
  scp -q "$jar" "pluto:$stage/diaries-0028-reviewed-migration-fat.jar"
  for name in 0028-dispositions.csv 0028-image-decisions.csv 0028-v2-preservation-decisions.PRIVATE.csv PREPARATION-RESULT.json SHA256SUMS.txt; do
    scp -q "$prepared/$name" "pluto:$stage/reviewed/$name"
  done
  # Verify from a fresh SSH session; catches missing stage, permission or
  # transfer corruption before declaring the runtime inputs ready.
  ssh pluto "test -d '$stage/reviewed' && \
    test \"\$(stat -c %a '$stage')\" = 700 && \
    printf '%s  %s\\n' '$hash' '$stage/diaries-0028-reviewed-migration-fat.jar' | sha256sum -c -" || {
    echo 'FAIL: staged JAR not retained/private/verified across SSH sessions' >&2; exit 1;
  }
  echo "PINNED_0028_JAR_SHA256=$hash"
  echo 'PASS: private 0028 inputs staged into a single transient pluto runtime directory'
  echo 'PRODUCTION APPLY NOT AUTHORISED; NO database or service change made by this script'
) || { echo 'FAIL: private staging incomplete; inspect transient stage without deleting evidence'; exit 1; }
