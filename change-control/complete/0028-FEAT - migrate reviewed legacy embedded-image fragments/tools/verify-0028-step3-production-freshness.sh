#!/usr/bin/env bash
# Windows PC, Cygwin terminal. Fresh read-only production inventory and independent
# comparison of 0028's frozen manifest. No migration, backups, edits or MQTT RPCs.
# Isolate fail-fast in a subshell; never change parent interactive shell options.
(
  set -euo pipefail
  feature='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
  manifest="$feature/evidence/Step 1/private/20261123T144651Z-reviewed-manifest-prepared"
  baseline="$feature/evidence/Step 1/private/20261123T143827Z-post0052-readonly/current/current-schema-snapshot.PRIVATE.csv"
  checker="$feature/tools/0028-step3-freshness.py"
  media="${DIARIES_0028_SOURCE_FILES_ROOT:-/cygdrive/p/nancy-and-ronald-maxwell/documents/sea-captains-chest/diaries-content/files}"
  test -d .git -o -f .git || { echo 'FAIL: run in Windows Diaries parent Git checkout' >&2; exit 1; }
  test -f "$feature/IMPLEMENTATION-STEPS.md" || { echo 'FAIL: Diaries feature directory not found' >&2; exit 1; }
  test -f "$manifest/PREPARATION-RESULT.json" || { echo 'FAIL: accepted prepared manifest not found' >&2; exit 1; }
  test -f "$baseline" || { echo 'FAIL: accepted previous production snapshot missing' >&2; exit 1; }
  test -d "$media" || { echo 'FAIL: NAS Files-root unavailable (DIARIES_0028_SOURCE_FILES_ROOT)' >&2; exit 1; }
  test -f "$checker" || { echo 'FAIL: Step 3 freshness verifier missing' >&2; exit 1; }
  grep -Fxq '/evidence/Step 3/private/' "$feature/.gitignore" || { echo 'FAIL: private evidence is not Git-ignored' >&2; exit 1; }
  command -v python3 >/dev/null
  command -v ssh >/dev/null
  command -v sha256sum >/dev/null

  echo '=== Run focused read-only comparator regression suite ==='
  python3 -m unittest discover -s "$feature/tests" -p 'test_step3_freshness.py' -v
  echo '=== Verify frozen manifest checksums ==='
  ( cd "$manifest" && sha256sum -c SHA256SUMS.txt )
  stamp=$(date -u +%Y%m%dT%H%M%SZ)
  out="$feature/evidence/Step 3/private/${stamp}-production-freshness"
  test ! -e "$out" || { echo 'FAIL: evidence folder already exists' >&2; exit 1; }
  mkdir -p "$out"
  chmod 700 "$out"
  echo "PRIVATE fresh production-readiness evidence: $out"
  {
    echo "UTC: $stamp"
    git branch --show-current
    git rev-parse HEAD
    git status --short
    git submodule status
    for name in diaries-client diaries-responder diaries-web; do
      printf '%s\t' "$name"
      git -C "$name" rev-parse HEAD
      git -C "$name" status --short
    done
    sha256sum "$manifest"/0028-dispositions.csv "$manifest"/0028-image-decisions.csv \
      "$manifest"/0028-v2-preservation-decisions.PRIVATE.csv "$baseline"
  } > "$out/checkout-and-input-identity.txt" 2>&1

  echo '=== Production runtime identities from pluto (read-only Docker inspection) ==='
  ssh -o BatchMode=yes -T pluto '
    test "$(hostname -s)" = pluto || { echo "FAIL: SSH host is not pluto" >&2; exit 1; }
    echo "hostname: $(hostname -s)"
    echo "container | image tag | container ID | status"
    docker ps --filter name=diaries --format "{{.Names}} | {{.Image}} | {{.ID}} | {{.Status}}"
    echo "diaries image digests where locally available:"
    docker image ls --digests --format "{{.Repository}} | {{.Tag}} | {{.Digest}}" | grep diaries || true
  ' > "$out/pluto-runtime-readonly.txt" 2>&1 || {
    echo 'FAIL: production Docker identity collection failed; see PRIVATE output' >&2; exit 1;
  }
  echo 'PASS: pluto runtime identity inventory recorded (compatibility review still required)'

  echo '=== Fresh current-schema COPY SELECT from production PostgreSQL ==='
  python3 "$feature/tools/step1_inventory.py" --ssh-host pluto --output "$out/current"

  echo '=== Compare reviewed 72 sources and all approved Image Files against production ==='
  python3 "$checker" --manifest "$manifest" --baseline-snapshot "$baseline" \
    --snapshot "$out/current/current-schema-snapshot.PRIVATE.csv" \
    --candidates "$out/current/0028-image-decisions.UNREVIEWED.csv" \
    --files-root "$media" --output "$out/FRESH-PRODUCTION-PREFLIGHT.json"
  echo 'PASS: 0028 production source/media freshness at snapshot time; NO production writes'
  echo 'PENDING: writer-stop, fresh restore points, compatibility decision, explicit production approval'
  echo "Private evidence: $out"
)
# Keep this subshell outside an AND/OR list or an if-condition. Bash suppresses
# errexit inside a compound command whose status is tested by && or ||. A
# failed comparator must never be followed by a misleading overall PASS.
rc=$?
if [ "$rc" -eq 0 ]; then
  echo '0028 FRESH SOURCE PREFLIGHT: PASS; PRODUCTION APPLY NOT AUTHORISED'
else
  echo "FAIL: 0028 fresh production preflight incomplete or BLOCKED (exit $rc)" >&2
  echo 'No database, MQTT, backup snapshot, deployment or migration modifications were attempted.' >&2
  exit "$rc"
fi
