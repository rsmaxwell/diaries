#!/usr/bin/env bash
# Windows PC Cygwin. Offline compare most recent private artifact/runtime evidence.
# Never creates backups, stops writers or runs migration.
(
  set -euo pipefail
  umask 077
  feature='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
  base="$feature/evidence/Step 3/private"
  tool="$feature/tools/0028_step3_release_candidate.py"
  recovery="$base/20261124T142644Z-retained-restore-and-writers/READINESS-RESULT.json"
  test -f "$recovery" && test -f "$tool" || { echo 'FAIL: prior approved recovery receipt or tool missing' >&2; exit 2; }
  mapfile -t artifacts < <(find "$base" -mindepth 1 -maxdepth 1 -type d -name '*-release-artifact' -print | sort)
  mapfile -t runtimes < <(find "$base" -mindepth 1 -maxdepth 1 -type d -name '*-release-runtime' -print | sort)
  test "${#artifacts[@]}" -ge 1 && test "${#runtimes[@]}" -ge 1 || {
    echo 'FAIL: first run the release artifact build and live runtime inventory scripts' >&2; exit 2;
  }
  artifact=${artifacts[${#artifacts[@]}-1]}
  runtime="${runtimes[${#runtimes[@]}-1]}/pluto-release-runtime.json"
  stamp=$(date -u +%Y%m%dT%H%M%SZ)
  out="$base/${stamp}-final-release-candidate"
  test ! -e "$out" || { echo 'FAIL: refusing to overwrite existing evidence' >&2; exit 2; }
  mkdir -p "$out"
  python3 "$tool" --artifact-dir "$artifact" --runtime "$runtime" --recovery "$recovery" --output "$out/RELEASE-CANDIDATE.json"
  echo "Private candidate: $out"
  echo 'NO PRODUCTION SERVICES WERE ALTERED; PRODUCTION APPLY NOT AUTHORISED'
)