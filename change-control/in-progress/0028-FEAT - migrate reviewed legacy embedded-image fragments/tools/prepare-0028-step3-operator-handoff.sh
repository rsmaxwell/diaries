#!/usr/bin/env bash
# WINDOWS / Cygwin, Diaries parent checkout. One read-only pluto Java probe;
# all other checks are local evidence. NO writer or backup changes.
(
  set -euo pipefail
  umask 077
  feature='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
  base="$feature/evidence/Step 3/private"
  tool="$feature/tools/step3_0028_maintenance_handoff.py"
  test -f "$feature/IMPLEMENTATION-STEPS.md" && test -f "$tool" && test -d diaries-responder || {
    echo 'FAIL: run in the Windows Diaries parent root after applying the 0028 ZIP' >&2; exit 2;
  }
  for cmd in python3 git sha256sum ssh; do
    command -v "$cmd" >/dev/null 2>&1 || { echo "FAIL: missing $cmd" >&2; exit 2; }
  done
  mapfile -t artifact_dirs < <(find "$base" -mindepth 1 -maxdepth 1 -type d -name '*-release-artifact' -print | sort)
  mapfile -t runtime_dirs < <(find "$base" -mindepth 1 -maxdepth 1 -type d -name '*-release-runtime' -print | sort)
  mapfile -t candidate_dirs < <(find "$base" -mindepth 1 -maxdepth 1 -type d -name '*-final-release-candidate' -print | sort)
  if test "${#artifact_dirs[@]}" -lt 1 || test "${#runtime_dirs[@]}" -lt 1 || test "${#candidate_dirs[@]}" -lt 1; then
    echo 'FAIL: prior release-artifact, runtime survey and candidate evidence must exist' >&2; exit 2
  fi
  artifact=${artifact_dirs[${#artifact_dirs[@]}-1]}
  runtime="${runtime_dirs[${#runtime_dirs[@]}-1]}/pluto-release-runtime.json"
  candidate="${candidate_dirs[${#candidate_dirs[@]}-1]}/RELEASE-CANDIDATE.json"
  recovery="$base/20261124T142644Z-retained-restore-and-writers/READINESS-RESULT.json"
  test -s "$runtime" && test -s "$candidate" && test -s "$recovery" || {
    echo 'FAIL: accepted recovery and release evidence must be available' >&2; exit 2
  }
  source_commit=$(git -C diaries-responder rev-parse HEAD)
  test -z "$(git -C diaries-responder status --porcelain)" || {
    echo 'FAIL: responder source is dirty; do not issue a frozen release handoff' >&2; exit 2
  }
  stamp=$(date -u +%Y%m%dT%H%M%SZ)
  out="$base/${stamp}-operator-handoff"
  test ! -e "$out" || { echo 'FAIL: refusing to overwrite evidence' >&2; exit 2; }
  mkdir -p "$out"
  echo '=== Offline handoff regression checks ==='
  python3 "$feature/tests/test_step3_0028_maintenance_handoff.py"
  echo '=== Bind accepted release/recovery identities (LOCAL only) ==='
  python3 "$tool" --candidate "$candidate" --runtime "$runtime" --recovery "$recovery" \
    --artifact-dir "$artifact" --source-commit "$source_commit" \
    --output "$out/RELEASE-HANDOFF.json"
  echo '=== pluto: live Java compatibility probe (READ-ONLY) ==='
  if ! ssh -o BatchMode=yes -o ConnectTimeout=15 pluto \
      'docker exec diaries-responder java -version' > "$out/pluto-java-version.txt" 2>&1; then
    echo 'FAIL: could not inspect current responder Java; inspect private receipt' >&2; exit 2
  fi
  python3 - "$out/pluto-java-version.txt" "$out/RELEASE-HANDOFF.json" <<'PY'
import json, re, sys
from pathlib import Path
text=Path(sys.argv[1]).read_text(encoding='utf-8',errors='replace')
expected=json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))['requiredJavaMajor']
match=re.search(r'(?:openjdk|java)(?:\s+version)?\s+["\']?(\d+)', text, re.I)
if not match or int(match.group(1)) != expected:
    raise SystemExit('FAIL: production responder Java version not verified as Java {}'.format(expected))
print('PASS: current production responder JVM is Java {}'.format(expected))
PY
  {
    echo '=== Windows parent checkout (read only) ==='
    git branch --show-current
    git rev-parse HEAD
    git submodule status
    echo '=== Parent-pinned responder revision ==='
    git ls-tree HEAD diaries-responder
    echo '=== Working responder revision ==='
    git -C diaries-responder rev-parse HEAD
    echo '=== Working tree summaries ==='
    git status --short
    git -C diaries-responder status --short
    echo '=== Pinned migration JAR SHA-256 ==='
    sha256sum "$artifact/diaries-0028-reviewed-migration-fat.jar"
  } > "$out/GIT-AND-JAR-IDENTITIES.txt" 2>&1
  parent_pin=$(git ls-tree HEAD diaries-responder | awk '{print $3}')
  if test "$parent_pin" != "$source_commit"; then
    echo "OPEN: parent currently pins responder $parent_pin, not $source_commit; reconcile before release"
  else
    echo 'PASS: parent submodule pointer matches migration source'
  fi
  echo "PASS: operator handoff evidence: $out"
  echo 'OPEN: writer isolation, fresh immutable recovery point, production dry-run, approval'
  echo 'PRODUCTION APPLY NOT AUTHORISED'
) && echo '0028 HANDOFF: PREPARED READ-ONLY; PRODUCTION APPLY NOT AUTHORISED' || {
  rc=$?
  echo "FAIL: operator handoff incomplete (exit $rc); do not execute production operations" >&2
  exit "$rc"
}
