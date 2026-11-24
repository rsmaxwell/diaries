#!/usr/bin/env bash
# Windows 11 Cygwin: run from Diaries parent repository root after applying ZIP.
# Stages existing accepted evidence reports, then invokes the pinned migration on pluto.
# NEVER rerun after a partial apply; inspect migration journal first.
(
  set -euo pipefail
  feature='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
  b="$feature/reports/STEP3-SESSION-INDEPENDENT-PRIVATE-STAGE-REPAIR-20261124.md"
  r="$feature/reports/STEP2-OWNER-OBSERVED-GUI-ACCEPTANCE-20261124.md"
  runner="$feature/tools/0028-pluto-production-apply.py"
  test -s "$b" && test -s "$r" && test -s "$runner" || { echo 'FAIL: required source report/script missing'; exit 1; }
  grep -q '20261124-173416Z' "$b" && grep -q '20261124-172811Z' "$b" || { echo 'FAIL: recovery identities not in accepted report'; exit 1; }
  grep -q '20261123T185712Z-isolated-db-rehearsal' "$r" || { echo 'FAIL: isolated rehearsal identity absent'; exit 1; }
  backup_sha="$(sha256sum "$b" | awk '{print $1}')"
  rehearsal_sha="$(sha256sum "$r" | awk '{print $1}')"
  jar_sha='9a2910515bbe0929c93c0557f91c2b27b8323bb9da61fb2573a0ff9b20c209a1'
  echo '=== Stage accepted report evidence (read-only copies) ==='
  ssh pluto 'mkdir -p -m 700 /run/diaries-0028-production-migration-input/accepted-evidence && chmod 700 /run/diaries-0028-production-migration-input/accepted-evidence'
  ssh pluto 'cat > /run/diaries-0028-production-migration-input/accepted-evidence/backup.md && chmod 600 /run/diaries-0028-production-migration-input/accepted-evidence/backup.md' < "$b"
  ssh pluto 'cat > /run/diaries-0028-production-migration-input/accepted-evidence/rehearsal.md && chmod 600 /run/diaries-0028-production-migration-input/accepted-evidence/rehearsal.md' < "$r"
  echo '=== Execute approved 71-conversion production apply ==='
  ssh pluto "python3 - apply $jar_sha $backup_sha $rehearsal_sha" < "$runner"
  echo 'PASS: production apply process returned successful status; KEEP PRODUCTION ISOLATED pending MQTT replay/UI verification'
) && echo 'PASS: apply invocation completed' || echo 'FAIL: investigate apply/journal, keep production isolated; do not rerun automatically'
