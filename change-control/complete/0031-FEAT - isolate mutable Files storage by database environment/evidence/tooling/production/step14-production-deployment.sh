#!/usr/bin/env bash
set -euo pipefail

RESPONDER_STOPPED_BY_SCRIPT=0

fail() {
    echo "ERROR: 0031 Step 14: $*" >&2
    if [[ "${RESPONDER_STOPPED_BY_SCRIPT}" == "1" ]]; then
        echo "NOTICE: diaries-responder was stopped by Step 14 and is intentionally being left stopped for investigation." >&2
    fi
    exit 1
}

usage() {
    cat >&2 <<'USAGE'
Usage:
  step14-production-deployment.sh preflight
  step14-production-deployment.sh postflight PREFLIGHT_RUN_DIRECTORY

preflight must be run on production while the Step 13 responder write freeze is
still in force. It validates the deployed production mapping and Step 8 recovery
artifacts, captures immutable production/non-production controls, and writes a
redacted configuration review.

After the normal Ansible Diaries deployment has completed successfully, run
postflight with the exact preflight directory. It first proves the restarted
stack is healthy and serves an existing /files object, then briefly stops only
diaries-responder to compare durable controls and rerun the existing read-only
Step 12 reconciliation. The responder is restarted only after every check passes.
USAGE
    exit 2
}

[[ $# -ge 1 && $# -le 2 ]] || usage
ACTION="$1"
[[ "${ACTION}" == "preflight" || "${ACTION}" == "postflight" ]] || usage
if [[ "${ACTION}" == "preflight" ]]; then
    [[ $# -eq 1 ]] || usage
    PREFLIGHT_RUN=""
else
    [[ $# -eq 2 ]] || usage
    PREFLIGHT_RUN="$2"
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${PROJECT_DIR}/.env"
COMPOSE_FILE="${PROJECT_DIR}/compose.yaml"
MOSQUITTO_FILE="${PROJECT_DIR}/config/mosquitto/mosquitto.conf"
STEP12_RUNNER="${SCRIPT_DIR}/step12-reconcile-production.sh"
EVIDENCE_ROOT="${PROJECT_DIR}/data/0031-step14"

for path in "${ENV_FILE}" "${COMPOSE_FILE}" "${MOSQUITTO_FILE}"; do
    [[ -f "${path}" ]] || fail "Required deployed file not found: ${path}"
done
command -v docker >/dev/null 2>&1 || fail "docker was not found on PATH"
command -v python3 >/dev/null 2>&1 || fail "python3 was not found on PATH"
command -v sha256sum >/dev/null 2>&1 || fail "sha256sum was not found on PATH"

read_env_value() {
    local key="$1" line value
    line="$(grep -E "^[[:space:]]*${key}=" "${ENV_FILE}" | tail -n 1 || true)"
    [[ -n "${line}" ]] || return 1
    value="${line#*=}"
    value="${value%$'\r'}"
    if [[ "${value}" == \"*\" && "${value}" == *\" ]]; then value="${value:1:${#value}-2}"; fi
    if [[ "${value}" == \'*\' && "${value}" == *\' ]]; then value="${value:1:${#value}-2}"; fi
    printf '%s' "${value}"
}

FILES_DIR="$(read_env_value DIARIES_FILES_DIR || true)"
CONTENT_PATH="$(read_env_value DIARIES_NAS_CONTENT_PATH || true)"
DB_NAME="$(read_env_value DIARIES_DB_NAME || true)"
DB_USER="$(read_env_value DIARIES_DB_USERNAME || true)"
NAS_HOST="$(read_env_value DIARIES_NAS_HOST || true)"
NAS_SHARE="$(read_env_value DIARIES_NAS_SHARE || true)"
[[ "${FILES_DIR}" == "files" ]] || fail "Production DIARIES_FILES_DIR must be 'files'; found '${FILES_DIR}'"
[[ -n "${CONTENT_PATH}" && -n "${DB_NAME}" && -n "${DB_USER}" && -n "${NAS_HOST}" && -n "${NAS_SHARE}" ]] || \
    fail "Required production environment values are missing"

COMPOSE=(docker compose --file "${COMPOSE_FILE}" --env-file "${ENV_FILE}")
cd -- "${PROJECT_DIR}"
"${COMPOSE[@]}" config --quiet

service_is_running() {
    local service="$1"
    "${COMPOSE[@]}" ps --status running --services | grep -Fxq "${service}"
}

require_running() {
    local service="$1"
    service_is_running "${service}" || fail "Production service ${service} is not running"
}

require_responder_stopped() {
    if service_is_running diaries-responder; then
        fail "Production responder is running; the Step 13/14 write freeze is required for this phase"
    fi
}

container_id_all() {
    local service="$1"
    "${COMPOSE[@]}" ps --all --quiet "${service}" | head -n 1
}

nas_volume_name() {
    local cid volume
    cid="$(container_id_all diaries-responder)"
    [[ -n "${cid}" ]] || fail "Unable to locate the deployed diaries-responder container needed to resolve the NAS volume"
    volume="$(docker inspect -f '{{range .Mounts}}{{if eq .Destination "/data/files"}}{{.Name}}{{end}}{{end}}' "${cid}" 2>/dev/null || true)"
    [[ -n "${volume}" ]] || fail "Unable to resolve the named NAS volume from the responder /data/files mount"
    printf '%s' "${volume}"
}

capture_image_rows() {
    local output="$1"
    "${COMPOSE[@]}" exec -T diaries-db psql -X -v ON_ERROR_STOP=1 -U "${DB_USER}" -d "${DB_NAME}" \
        -c "COPY (SELECT id,version,relative_path,mime_type,original_filename,width,height,checksum,caption,alt_text FROM public.image ORDER BY id) TO STDOUT WITH (FORMAT csv, HEADER true, DELIMITER E'\\t');" \
        > "${output}"
}

capture_files_inventory() {
    local output="$1"
    "${COMPOSE[@]}" run --rm --no-deps --no-tty --pull never --entrypoint sh diaries-responder -c '
set -eu
find /data/files -type f -print | LC_ALL=C sort | while IFS= read -r file; do
  rel=${file#/data/files/}
  bytes=$(wc -c < "$file" | tr -d " ")
  hash_line=$(sha256sum "$file")
  hash=${hash_line%% *}
  printf "%s\t%s\t%s\n" "$rel" "$bytes" "$hash"
done
' > "${output}"
}

capture_nonproduction_inventory() {
    local output="$1" volume
    volume="$(nas_volume_name)"
    docker run --rm --pull never \
        -e CONTENT_PATH="${CONTENT_PATH}" \
        --mount "type=volume,src=${volume},dst=/nas,readonly" \
        postgres:18-alpine sh -c '
set -eu
base="/nas/${CONTENT_PATH#/}"
for root in "$base"/files-development-*; do
  [ -d "$root" ] || continue
  selector=${root##*/}
  find "$root" -type f -print | LC_ALL=C sort | while IFS= read -r file; do
    rel=${file#"$root"/}
    bytes=$(wc -c < "$file" | tr -d " ")
    hash_line=$(sha256sum "$file")
    hash=${hash_line%% *}
    printf "%s\t%s\t%s\t%s\n" "$selector" "$rel" "$bytes" "$hash"
  done
done
' > "${output}"
}

write_redacted_config() {
    local output="$1"
    python3 - "${ENV_FILE}" "${COMPOSE_FILE}" "${MOSQUITTO_FILE}" > "${output}" <<'PY'
import re
import sys
from pathlib import Path

env_path, compose_path, mosq_path = map(Path, sys.argv[1:])
values = {}
for raw in env_path.read_text(encoding="utf-8").splitlines():
    if not raw.strip() or raw.lstrip().startswith("#") or "=" not in raw:
        continue
    key, value = raw.split("=", 1)
    values[key.strip()] = value.strip()

print("0031-FEAT Step 14 redacted production configuration review")
print(f"environmentFile={env_path}")
for key in sorted(values):
    upper = key.upper()
    if any(token in upper for token in ("PASSWORD", "TOKEN")):
        value = "<redacted>"
    elif key == "DIARIES_NAS_USERNAME":
        value = "<redacted>"
    else:
        value = values[key]
    print(f"{key}={value}")

compose = compose_path.read_text(encoding="utf-8")
print("\ncomposeChecks:")
print("  dataFilesTarget=/data/files")
print("  dataFilesSubpath=${DIARIES_NAS_CONTENT_PATH}/${DIARIES_FILES_DIR}")
print("  sharedScansSubpath=${DIARIES_NAS_CONTENT_PATH}/diaries")
print(f"  containsMutableSelector={'yes' if 'subpath: ${DIARIES_NAS_CONTENT_PATH}/${DIARIES_FILES_DIR}' in compose else 'no'}")
print(f"  containsHardCodedMutableFiles={'yes' if 'subpath: ${DIARIES_NAS_CONTENT_PATH}/files' in compose else 'no'}")
print(f"  mentionsLocalEnv={'yes' if 'local.env' in compose else 'no'}")

queue = []
for line in mosq_path.read_text(encoding="utf-8").splitlines():
    if re.match(r"^max_(?:inflight|queued)_messages\s+", line.strip()):
        queue.append(line.strip())
print("\nmosquittoFlowControl:")
for line in queue:
    print(f"  {line}")
PY
}

verify_no_local_override_participation() {
    local candidate
    for candidate in "${COMPOSE_FILE}" "${PROJECT_DIR}/scripts/start.sh"; do
        [[ -f "${candidate}" ]] || continue
        if grep -Fq 'local.env' "${candidate}"; then
            fail "Production deployment path unexpectedly references local.env: ${candidate}"
        fi
    done
    if [[ -f /etc/systemd/system/diaries-compose.service ]] && grep -Fq 'local.env' /etc/systemd/system/diaries-compose.service; then
        fail "Production systemd unit unexpectedly references local.env"
    fi
}

verify_step8_database_backup() {
    local output="$1" manifest details backup backup_sha sidecar sidecar_sha actual
    manifest="$(find "${PROJECT_DIR}/data/0031-step8" -maxdepth 1 -type f -name 'production-database-backup-*.json' -print 2>/dev/null | LC_ALL=C sort -r | head -n 1)"
    [[ -n "${manifest}" && -f "${manifest}" ]] || fail "No Step 8 production database-backup manifest remains under ${PROJECT_DIR}/data/0031-step8"
    details="$(python3 - "${manifest}" <<'PY'
import json, sys
m=json.load(open(sys.argv[1], encoding='utf-8'))
print(m.get('databaseBackupFile',''))
print(m.get('databaseBackupSha256',''))
print(m.get('databaseSidecarFile',''))
print(m.get('databaseSidecarSha256',''))
PY
)"
    backup="$(sed -n '1p' <<<"${details}")"
    backup_sha="$(sed -n '2p' <<<"${details}")"
    sidecar="$(sed -n '3p' <<<"${details}")"
    sidecar_sha="$(sed -n '4p' <<<"${details}")"
    [[ -s "${backup}" ]] || fail "Step 8 production database backup is missing/empty: ${backup}"
    [[ -s "${sidecar}" ]] || fail "Step 8 production database sidecar is missing/empty: ${sidecar}"
    actual="$(sha256sum "${backup}" | awk '{print $1}')"
    [[ "${actual}" == "${backup_sha}" ]] || fail "Step 8 production database backup SHA-256 no longer matches its manifest"
    actual="$(sha256sum "${sidecar}" | awk '{print $1}')"
    [[ "${actual}" == "${sidecar_sha}" ]] || fail "Step 8 production database sidecar SHA-256 no longer matches its manifest"
    cat > "${output}" <<CHECK
PASS: Step 8 production database backup and sidecar remain available and match their recorded SHA-256 values.
manifest=${manifest}
backup=${backup}
backupSha256=${backup_sha}
sidecar=${sidecar}
sidecarSha256=${sidecar_sha}
CHECK
}

verify_step8_files_snapshot() {
    local output="$1" manifest_copy="$2" volume snapshot_manifest snapshot_dir details expected_hash expected_count actual_hash actual_count
    volume="$(nas_volume_name)"
    snapshot_manifest="$(docker run --rm --pull never \
        -e CONTENT_PATH="${CONTENT_PATH}" \
        --mount "type=volume,src=${volume},dst=/nas,readonly" \
        postgres:18-alpine sh -c '
set -eu
root="/nas/${CONTENT_PATH#/}/.0031-backups"
[ -d "$root" ] || exit 3
find "$root" -mindepth 2 -maxdepth 2 -type f -path "*/step8-*/SNAPSHOT-MANIFEST.json" -print | LC_ALL=C sort -r | head -n 1
' || true)"
    [[ -n "${snapshot_manifest}" ]] || fail "Unable to find the Step 8 Files rollback SNAPSHOT-MANIFEST.json on the production NAS share"
    docker run --rm --pull never \
        --mount "type=volume,src=${volume},dst=/nas,readonly" \
        postgres:18-alpine cat "${snapshot_manifest}" > "${manifest_copy}"
    details="$(python3 - "${manifest_copy}" <<'PY'
import json, sys
m=json.load(open(sys.argv[1], encoding='utf-8'))
if m.get('captureType') != '0031-step8-shared-files-premigration-snapshot':
    raise SystemExit('unexpected captureType')
if m.get('sourceFilesDir') != 'files' or not m.get('inventoriesIdentical'):
    raise SystemExit('snapshot identity/inventory flag is not the frozen Step 8 value')
print(m['snapshotInventory']['sha256'])
print(m['snapshotFileCount'])
PY
)" || fail "Step 8 Files snapshot manifest is invalid"
    expected_hash="$(sed -n '1p' <<<"${details}")"
    expected_count="$(sed -n '2p' <<<"${details}")"
    snapshot_dir="${snapshot_manifest%/SNAPSHOT-MANIFEST.json}"
    actual_hash="$(docker run --rm --pull never \
        --mount "type=volume,src=${volume},dst=/nas,readonly" \
        postgres:18-alpine sha256sum "${snapshot_dir}/SNAPSHOT-SHA256.tsv" | awk '{print $1}')"
    [[ "${actual_hash}" == "${expected_hash}" ]] || fail "Step 8 Files snapshot inventory SHA-256 no longer matches the rollback manifest"
    actual_count="$(docker run --rm --pull never \
        --mount "type=volume,src=${volume},dst=/nas,readonly" \
        postgres:18-alpine sh -c 'find "$1/files" -type f -print | wc -l' sh "${snapshot_dir}" | tr -d ' ')"
    [[ "${actual_count}" == "${expected_count}" ]] || fail "Step 8 Files snapshot file count no longer matches the rollback manifest"
    cat > "${output}" <<CHECK
PASS: Step 8 Files rollback snapshot remains available on the production NAS share.
manifest=${snapshot_manifest}
snapshotInventorySha256=${expected_hash}
snapshotFileCount=${expected_count}
CHECK
}

capture_service_status() {
    local output="$1" service cid state health
    : > "${output}"
    while IFS= read -r service; do
        [[ -n "${service}" ]] || continue
        cid="$("${COMPOSE[@]}" ps --all --quiet "${service}" | head -n 1)"
        [[ -n "${cid}" ]] || fail "Compose service ${service} has no container after deployment"
        state="$(docker inspect -f '{{.State.Status}}' "${cid}")"
        health="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "${cid}")"
        printf '%s\t%s\t%s\n' "${service}" "${state}" "${health}" >> "${output}"
        [[ "${state}" == "running" ]] || fail "Compose service ${service} is not running (state=${state})"
        [[ "${health}" == "none" || "${health}" == "healthy" ]] || fail "Compose service ${service} is not healthy (health=${health})"
    done < <("${COMPOSE[@]}" config --services)
}

require_responder_synchronised() {
    local cid started attempt logs
    cid="$("${COMPOSE[@]}" ps --quiet diaries-responder | head -n 1)"
    [[ -n "${cid}" ]] || fail "diaries-responder has no running container while checking startup synchronisation"
    started="$(docker inspect -f '{{.State.StartedAt}}' "${cid}")"
    for attempt in $(seq 1 90); do
        logs="$(docker logs --since "${started}" "${cid}" 2>&1 || true)"
        if grep -Fq 'synchronise: ok' <<<"${logs}"; then
            echo "PASS: responder startup retained-tree synchronisation completed successfully."
            return 0
        fi
        if [[ "$(docker inspect -f '{{.State.Running}}' "${cid}" 2>/dev/null || true)" != "true" ]]; then
            fail "diaries-responder stopped before startup synchronisation completed"
        fi
        sleep 2
    done
    fail "diaries-responder did not log 'synchronise: ok' for the current container start"
}

verify_files_route() {
    local output="$1" rel encoded code physical_hash served_hash tmp_path
    rel="$("${COMPOSE[@]}" exec -T diaries-db psql -X -A -t -v ON_ERROR_STOP=1 -U "${DB_USER}" -d "${DB_NAME}" \
        -c "SELECT relative_path FROM public.image WHERE relative_path IS NOT NULL AND relative_path <> '' ORDER BY id LIMIT 1;" | tr -d '\r' | head -n 1)"
    [[ -n "${rel}" ]] || fail "Production Image catalogue has no relative_path available for the non-destructive /files route check"
    encoded="$(python3 - "${rel}" <<'PY'
import sys
from urllib.parse import quote
print('/'.join(quote(part, safe='') for part in sys.argv[1].split('/')))
PY
)"
    tmp_path="/tmp/0031-step14-files-check.$$"
    code="$("${COMPOSE[@]}" exec -T diaries-responder curl --silent --show-error --output "${tmp_path}" --write-out '%{http_code}' "http://localhost:8081/files/${encoded}")"
    [[ "${code}" == "200" ]] || fail "Existing production /files object returned HTTP ${code}: ${rel}"
    physical_hash="$("${COMPOSE[@]}" exec -T diaries-responder sha256sum "/data/files/${rel}" | awk '{print $1}')"
    served_hash="$("${COMPOSE[@]}" exec -T diaries-responder sha256sum "${tmp_path}" | awk '{print $1}')"
    "${COMPOSE[@]}" exec -T diaries-responder rm -f "${tmp_path}"
    [[ "${physical_hash}" == "${served_hash}" ]] || fail "Bytes served by /files differ from the selected production physical file: ${rel}"
    cat > "${output}" <<CHECK
PASS: existing production /files route served the same bytes as /data/files.
relativePath=${rel}
httpStatus=${code}
sha256=${served_hash}
CHECK
}

require_step13_handoff_unchanged() {
    local image_rows="$1" files_inventory="$2" output="$3" prior
    prior="$(find "${PROJECT_DIR}/data/0031-step13" -mindepth 1 -maxdepth 1 -type d -name 'production-after-*' -print 2>/dev/null | LC_ALL=C sort -r | head -n 1)"
    [[ -n "${prior}" ]] || fail "No Step 13 production-after control is available for the Step 14 hand-off check"
    [[ -f "${prior}/IMAGE-ROWS.tsv" && -f "${prior}/FILES-INVENTORY.tsv" ]] || fail "Latest Step 13 production-after control is incomplete: ${prior}"
    cmp -s -- "${prior}/IMAGE-ROWS.tsv" "${image_rows}" || fail "Production Image rows drifted after the authoritative Step 13 AFTER control"
    cmp -s -- "${prior}/FILES-INVENTORY.tsv" "${files_inventory}" || fail "Production Files bytes drifted after the authoritative Step 13 AFTER control"
    cat > "${output}" <<CHECK
PASS: Step 14 preflight durable controls match the latest Step 13 production AFTER control byte-for-byte.
step13After=${prior}
CHECK
}

TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
mkdir -p -- "${EVIDENCE_ROOT}"

if [[ "${ACTION}" == "preflight" ]]; then
    RUN_DIR="${EVIDENCE_ROOT}/preflight-${TIMESTAMP}"
    mkdir -p -- "${RUN_DIR}"
    exec > >(tee -a "${RUN_DIR}/RUN.txt") 2>&1

    echo "0031-FEAT Step 14 production preflight"
    echo "Captured: $(date --iso-8601=seconds)"
    echo "Project: ${PROJECT_DIR}"
    echo

    require_running diaries-db
    require_responder_stopped
    verify_no_local_override_participation
    grep -Fq 'subpath: ${DIARIES_NAS_CONTENT_PATH}/${DIARIES_FILES_DIR}' "${COMPOSE_FILE}" || \
        fail "Deployed Compose file does not select mutable /data/files through DIARIES_FILES_DIR"
    if grep -Fq 'subpath: ${DIARIES_NAS_CONTENT_PATH}/files' "${COMPOSE_FILE}"; then
        fail "Deployed Compose file hard-codes the mutable production files source instead of the explicit selector"
    fi

    write_redacted_config "${RUN_DIR}/REDACTED-CONFIG.txt"
    verify_step8_database_backup "${RUN_DIR}/STEP8-DATABASE-BACKUP-CHECK.txt"
    verify_step8_files_snapshot "${RUN_DIR}/STEP8-FILES-SNAPSHOT-CHECK.txt" "${RUN_DIR}/STEP8-FILES-SNAPSHOT-MANIFEST.json"
    capture_image_rows "${RUN_DIR}/IMAGE-ROWS.tsv"
    capture_files_inventory "${RUN_DIR}/FILES-INVENTORY.tsv"
    capture_nonproduction_inventory "${RUN_DIR}/NONPRODUCTION-FILES-INVENTORY.tsv"
    require_step13_handoff_unchanged "${RUN_DIR}/IMAGE-ROWS.tsv" "${RUN_DIR}/FILES-INVENTORY.tsv" "${RUN_DIR}/STEP13-HANDOFF-CHECK.txt"

    cat > "${RUN_DIR}/PAIR.txt" <<PAIR
feature=0031-FEAT
step=14
phase=preflight
capturedAt=$(date --iso-8601=seconds)
DIARIES_FILES_DIR=${FILES_DIR}
physicalNasRoot=//${NAS_HOST}/${NAS_SHARE}/${CONTENT_PATH%/}/${FILES_DIR}
dockerFilesRoot=/data/files
localOverrideParticipates=false
productionResponderRunning=false
PAIR

    echo
    echo "PASS: Step 14 production preflight is clean."
    echo "Production responder remains stopped for the normal Ansible deployment."
    echo "Evidence: ${RUN_DIR}"
    exit 0
fi

[[ -d "${PREFLIGHT_RUN}" ]] || fail "Preflight run directory does not exist: ${PREFLIGHT_RUN}"
PREFLIGHT_RUN="$(cd -- "${PREFLIGHT_RUN}" && pwd)"
for required in IMAGE-ROWS.tsv FILES-INVENTORY.tsv NONPRODUCTION-FILES-INVENTORY.tsv REDACTED-CONFIG.txt STEP8-DATABASE-BACKUP-CHECK.txt STEP8-FILES-SNAPSHOT-CHECK.txt; do
    [[ -f "${PREFLIGHT_RUN}/${required}" ]] || fail "Preflight evidence is incomplete; missing ${required}"
done

RUN_DIR="${EVIDENCE_ROOT}/postflight-${TIMESTAMP}"
mkdir -p -- "${RUN_DIR}"
exec > >(tee -a "${RUN_DIR}/RUN.txt") 2>&1

echo "0031-FEAT Step 14 production postflight"
echo "Captured: $(date --iso-8601=seconds)"
echo "Preflight: ${PREFLIGHT_RUN}"
echo

# The playbook must have restarted the complete production stack successfully
# before we deliberately freeze only the responder for deterministic durable
# comparisons and the existing Step 12 dry-run reconciliation.
capture_service_status "${RUN_DIR}/SERVICE-STATUS-AFTER-DEPLOY.tsv"
require_responder_synchronised

grep -Eq '^max_inflight_messages[[:space:]]+20([[:space:]]|$)' "${MOSQUITTO_FILE}" || \
    fail "Deployed production Mosquitto config does not retain max_inflight_messages 20"
grep -Eq '^max_queued_messages[[:space:]]+0([[:space:]]|$)' "${MOSQUITTO_FILE}" || \
    fail "Deployed production Mosquitto config has not adopted max_queued_messages 0"
"${COMPOSE[@]}" exec -T diaries-mqtt sh -c "grep -Eq '^max_inflight_messages[[:space:]]+20([[:space:]]|$)' /mosquitto/config/mosquitto.conf && grep -Eq '^max_queued_messages[[:space:]]+0([[:space:]]|$)' /mosquitto/config/mosquitto.conf" || \
    fail "Running production broker has not loaded the Step 13 retained-snapshot flow-control policy"

write_redacted_config "${RUN_DIR}/REDACTED-CONFIG-AFTER-DEPLOY.txt"
verify_no_local_override_participation
verify_files_route "${RUN_DIR}/FILES-ROUTE-CHECK.txt"
"${COMPOSE[@]}" logs --no-color --tail 500 diaries-responder > "${RUN_DIR}/RESPONDER-STARTUP-LOG.txt" 2>&1 || true

# Freeze only the responder after proving successful startup. If any durable
# check fails from here, leave it stopped rather than re-enable writes on an
# unexplained production state.
echo "Stopping diaries-responder temporarily for deterministic read-only verification..."
"${COMPOSE[@]}" stop diaries-responder
RESPONDER_STOPPED_BY_SCRIPT=1
require_responder_stopped
require_running diaries-db

capture_image_rows "${RUN_DIR}/IMAGE-ROWS.tsv"
capture_files_inventory "${RUN_DIR}/FILES-INVENTORY.tsv"
capture_nonproduction_inventory "${RUN_DIR}/NONPRODUCTION-FILES-INVENTORY.tsv"

cmp -s -- "${PREFLIGHT_RUN}/IMAGE-ROWS.tsv" "${RUN_DIR}/IMAGE-ROWS.tsv" || \
    fail "Production Image catalogue changed across the Step 14 deployment"
cmp -s -- "${PREFLIGHT_RUN}/FILES-INVENTORY.tsv" "${RUN_DIR}/FILES-INVENTORY.tsv" || \
    fail "Production mutable Files bytes changed across the Step 14 deployment"
cmp -s -- "${PREFLIGHT_RUN}/NONPRODUCTION-FILES-INVENTORY.tsv" "${RUN_DIR}/NONPRODUCTION-FILES-INVENTORY.tsv" || \
    fail "A non-production files-development-* root changed during the Step 14 production deployment window"

[[ -x "${STEP12_RUNNER}" ]] || fail "Step 12 production reconciliation helper is missing/not executable: ${STEP12_RUNNER}"
echo "Running the existing Step 12 read-only reconciliation against the deployed production pair..."
if "${STEP12_RUNNER}" --write-freeze-confirmed 2>&1 | tee "${RUN_DIR}/RECONCILIATION.txt"; then
    :
else
    rc=${PIPESTATUS[0]}
    fail "Read-only production reconciliation failed with exit code ${rc}"
fi
RECONCILIATION_RUN="$(sed -n 's/^Evidence: //p' "${RUN_DIR}/RECONCILIATION.txt" | tail -n 1)"
[[ -n "${RECONCILIATION_RUN}" && -f "${RECONCILIATION_RUN}/STEP12-REPORT.json" ]] || \
    fail "Step 12 reconciliation passed without yielding its expected evidence path/report"
cp -- "${RECONCILIATION_RUN}/STEP12-REPORT.json" "${RUN_DIR}/RECONCILIATION-REPORT.json"
cp -- "${RECONCILIATION_RUN}/STEP12-REPORT.md" "${RUN_DIR}/RECONCILIATION-REPORT.md"

cat > "${RUN_DIR}/COMPARISON.txt" <<COMPARE
PASS: production Image catalogue is byte-for-byte unchanged across Step 14 deployment.
PASS: production mutable Files SHA-256 inventory is byte-for-byte unchanged across Step 14 deployment.
PASS: non-production files-development-* SHA-256 inventory is byte-for-byte unchanged across Step 14 deployment.
PASS: read-only production reconciliation still matches the Step 9 semantic baseline.
preflight=${PREFLIGHT_RUN}
postflight=${RUN_DIR}
reconciliation=${RECONCILIATION_RUN}
COMPARE

echo "Restarting diaries-responder after all deterministic controls passed..."
"${COMPOSE[@]}" up --detach --no-deps --wait diaries-responder
RESPONDER_STOPPED_BY_SCRIPT=0
require_responder_synchronised
capture_service_status "${RUN_DIR}/SERVICE-STATUS-FINAL.tsv"
verify_files_route "${RUN_DIR}/FILES-ROUTE-CHECK-FINAL.txt"

cat > "${RUN_DIR}/RESULT.txt" <<RESULT
PASS: 0031-FEAT Step 14 production deployment verification completed non-destructively.
preflight=${PREFLIGHT_RUN}
postflight=${RUN_DIR}
DIARIES_FILES_DIR=${FILES_DIR}
physicalNasRoot=//${NAS_HOST}/${NAS_SHARE}/${CONTENT_PATH%/}/${FILES_DIR}
dockerFilesRoot=/data/files
maxInflightMessages=20
maxQueuedMessages=0
productionImageAndFilesUnchanged=true
nonProductionFilesRootsUnchanged=true
readOnlyReconciliationPassed=true
finalResponderRunning=true
RESULT

echo
echo "PASS: Step 14 production deployment is healthy and non-destructive."
echo "Evidence: ${RUN_DIR}"
