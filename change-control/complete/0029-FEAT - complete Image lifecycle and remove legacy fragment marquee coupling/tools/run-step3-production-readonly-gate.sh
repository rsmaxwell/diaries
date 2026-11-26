#!/usr/bin/env bash
# 0029 Step 3 production evidence — READ ONLY. Run on Windows Cygwin in Diaries repo root.
set -euo pipefail
feature='change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling'
sql="$feature/tools/step3-production-preflight-readonly.sql"
evidence="$feature/evidence/step-3-production-readiness"
[[ -f "$sql" ]] || { echo "FAIL: missing $sql" >&2; exit 1; }
command -v ssh >/dev/null && command -v git >/dev/null && command -v sha256sum >/dev/null || { echo 'FAIL: prerequisites missing' >&2; exit 1; }
mkdir -p "$evidence"
stamp="$(date -u +%Y%m%d-%H%M%S)"
log="$evidence/production-readonly-${stamp}.log"
# Pipe all diagnostic output to the same evidence record, and propagate failures.
exec > >(tee "$log") 2>&1
printf '0029 STEP 3 PRODUCTION READ-ONLY GATE UTC=%s\n' "$(date -u --iso-8601=seconds)"
echo "Evidence: $log"
echo '=== Local source provenance (uncommitted changes intentionally preserved) ==='
git status --short --branch
git rev-parse HEAD
git submodule status
for module in diaries-client diaries-responder diaries-web; do
  echo "--- $module ---"
  git -C "$module" status --short --branch
  git -C "$module" rev-parse HEAD
done
sha256sum "$sql" "$feature/tools/step2-hybrid-schema-and-data.sql" "$feature/tools/step3-retire-marquee-page-id.sql" "$feature/tools/step3-restore-marquee-page-id.sql"
echo '=== Mango Ansible controller and Playbooks revisions ==='
ssh mango 'cd /home/richard/ansible-controller && git status --short --branch && git rev-parse HEAD && git submodule status && cd playbooks && git status --short --branch && git rev-parse HEAD'
echo '=== Pluto running Diaries images and health ==='
ssh pluto 'docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" | grep -E "NAMES|diaries-"'
echo '=== Pluto annual MQTT topic ACL (read-only) ==='
ssh pluto 'docker exec diaries-mosquitto cat /mosquitto/config/aclfile.txt | grep -n -E "^user diaries-(client|responder|web)$|^topic (read|readwrite) diaries/years/#$"' || true
echo '=== Pluto production backup timer and service state (read-only metadata) ==='
ssh pluto 'systemctl list-timers --all --no-pager | grep -Ei "diaries|backup" || true'
echo '=== PRODUCTION POSTGRESQL PRE-MIGRATION GATE ==='
# SQL goes over SSH stdin, no SQL file copied to production; psql runs read-only.
result="$(ssh pluto 'docker exec -i diaries-postgres sh -c '\''exec psql -X -v ON_ERROR_STOP=1 -A -t -F "|" -U "$POSTGRES_USER" -d "$POSTGRES_DB"'\''' < "$sql")"
printf '%s\n' "$result"
if ! grep -q '^GATE=PASS|' <<< "$result"; then
  echo 'FAIL: production dataset does not satisfy the guarded 11-row baseline. DO NOT DEPLOY.' >&2
  exit 1
fi
echo 'PASS: production SQL baseline matches the reviewed 11-record pre-hybrid dataset.'
echo 'NOT YET VERIFIED: new image builds, tested backup restore, mutable Files recovery, deployment approval.'
echo 'NO PRODUCTION WRITES performed by this script.'
