#!/usr/bin/env bash

set -euo pipefail

# 0031-FEAT Step 9: read-only production Image-catalogue reconciliation against
# the frozen pre-split shared Files tree. This script never runs 0024 apply.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_FILE="${PROJECT_DIR}/compose.yaml"
ENV_FILE="${PROJECT_DIR}/.env"
HOST_CONFIG="${PROJECT_DIR}/config/responder/responder.json"
RESPONDER_SERVICE="${DIARIES_RESPONDER_SERVICE:-diaries-responder}"
DB_SERVICE="${DIARIES_DB_SERVICE:-diaries-db}"
RESPONDER_CONFIG="${DIARIES_RESPONDER_CONFIG:-/config/responder.json}"
RESPONDER_JAR="${DIARIES_RESPONDER_JAR:-/opt/diaries/lib/diaries-responder.jar}"
MAIN_CLASS="com.rsmaxwell.diaries.responder.migration.migration0024.Migration0024ImageCatalogue"
TIMESTAMP="$(date '+%Y%m%d-%H%M%S')"
RUN_DIR="${PROJECT_DIR}/data/0031-step9/production-${TIMESTAMP}"
RECON_DIR="${RUN_DIR}/reconciliation"
STAGING_INVENTORY="${RUN_DIR}/STAGING-INVENTORY.tsv"
REPORT_JSON="${RUN_DIR}/STEP9-REPORT.json"
REPORT_MD="${RUN_DIR}/STEP9-REPORT.md"

fail() {
    echo "ERROR: $*" >&2
    exit 1
}

read_env_value() {
    local key="$1"
    local value
    value="$(sed -n "s/^${key}=//p" "${ENV_FILE}" | tail -n 1 | tr -d '\r')"
    printf '%s' "${value}"
}

for path in "${COMPOSE_FILE}" "${ENV_FILE}" "${HOST_CONFIG}"; do
    [[ -f "${path}" ]] || fail "Required production file not found: ${path}"
done
command -v docker >/dev/null 2>&1 || fail "docker was not found on PATH."
command -v python3 >/dev/null 2>&1 || fail "python3 was not found on PATH."

FILES_DIR="$(read_env_value DIARIES_FILES_DIR)"
[[ "${FILES_DIR}" == "files" ]] || fail "Step 9 production reconciliation must inspect the frozen pre-split selector 'files'; .env contains '${FILES_DIR}'."
NAS_HOST="$(read_env_value DIARIES_NAS_HOST)"
NAS_SHARE="$(read_env_value DIARIES_NAS_SHARE)"
NAS_CONTENT_PATH="$(read_env_value DIARIES_NAS_CONTENT_PATH)"
[[ -n "${NAS_HOST}" && -n "${NAS_SHARE}" && -n "${NAS_CONTENT_PATH}" ]] || fail "Production NAS host/share/content path is incomplete in .env."
PHYSICAL_FILES_ROOT="//${NAS_HOST}/${NAS_SHARE}/${NAS_CONTENT_PATH#/}/files"

COMPOSE=(docker compose --file "${COMPOSE_FILE}" --env-file "${ENV_FILE}")
cd -- "${PROJECT_DIR}"
"${COMPOSE[@]}" config --quiet

RUNNING_SERVICES="$("${COMPOSE[@]}" ps --status running --services)"
if grep -Fxq "${RESPONDER_SERVICE}" <<<"${RUNNING_SERVICES}"; then
    fail "Production responder '${RESPONDER_SERVICE}' is running. Preserve the Step 8 write freeze before Step 9."
fi
if ! grep -Fxq "${DB_SERVICE}" <<<"${RUNNING_SERVICES}"; then
    fail "Production database service '${DB_SERVICE}' is not running."
fi

mkdir -p -- "${RECON_DIR}"
[[ -z "$(find "${RECON_DIR}" -mindepth 1 -maxdepth 1 -print -quit)" ]] || fail "Reconciliation directory is not empty: ${RECON_DIR}"

CONTAINER_EVIDENCE_ROOT="/migration-evidence"
echo "0031-FEAT Step 9 - production shared-Files reconciliation"
echo "Project:                  ${PROJECT_DIR}"
echo "Database service:         ${DB_SERVICE}"
echo "Reconciled Files selector: files"
echo "Physical Files root:      ${PHYSICAL_FILES_ROOT}"
echo "Evidence:                 ${RUN_DIR}"
echo
echo "Running existing 0024 reconciliation in DRY-RUN mode only..."

"${COMPOSE[@]}" run \
    --rm \
    --no-deps \
    --no-tty \
    --pull never \
    --entrypoint java \
    --volume "${RUN_DIR}:${CONTAINER_EVIDENCE_ROOT}" \
    "${RESPONDER_SERVICE}" \
    -cp "${RESPONDER_JAR}" \
    "${MAIN_CLASS}" \
    --config "${RESPONDER_CONFIG}" \
    --output "${CONTAINER_EVIDENCE_ROOT}/reconciliation" \
    --mode dry-run

[[ -f "${RECON_DIR}/0024-summary.json" ]] || fail "0024-summary.json was not produced."
[[ -f "${RECON_DIR}/0024-create-plan.json" ]] || fail "0024-create-plan.json was not produced."
[[ -f "${RECON_DIR}/0024-conflicts.csv" ]] || fail "0024-conflicts.csv was not produced."

# The 0024 reconciler intentionally excludes .image-staging. Step 9 records that
# recovery/transient state separately, still read-only, from the same /data/files
# mount used by the reconciliation container.
printf 'relativePath\tsize\tsha256\n' > "${STAGING_INVENTORY}"
"${COMPOSE[@]}" run \
    --rm \
    --no-deps \
    --no-tty \
    --pull never \
    --entrypoint sh \
    "${RESPONDER_SERVICE}" \
    -c '
set -eu
root=/data/files/.image-staging
[ -d "$root" ] || exit 0
find "$root" -type f -print | sort | while IFS= read -r file; do
    rel=${file#/data/files/}
    size=$(wc -c < "$file" | tr -d " ")
    hash=$(sha256sum "$file")
    hash=${hash%% *}
    printf "%s\\t%s\\t%s\\n" "$rel" "$size" "$hash"
done
' >> "${STAGING_INVENTORY}"

SOURCE_IDENTITY="unknown"
if command -v git >/dev/null 2>&1 && git -C "${PROJECT_DIR}" rev-parse HEAD >/dev/null 2>&1; then
    SOURCE_IDENTITY="$(git -C "${PROJECT_DIR}" rev-parse HEAD)"
fi

python3 - "${RECON_DIR}" "${STAGING_INVENTORY}" "${REPORT_JSON}" "${REPORT_MD}" "${PHYSICAL_FILES_ROOT}" "${SOURCE_IDENTITY}" <<'PYREPORT'
import csv
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

recon = Path(sys.argv[1])
staging_path = Path(sys.argv[2])
report_json = Path(sys.argv[3])
report_md = Path(sys.argv[4])
physical_root = sys.argv[5]
source_identity = sys.argv[6]

summary = json.loads((recon / '0024-summary.json').read_text(encoding='utf-8'))
plan = json.loads((recon / '0024-create-plan.json').read_text(encoding='utf-8'))
with (recon / '0024-conflicts.csv').open(newline='', encoding='utf-8') as handle:
    conflicts = list(csv.DictReader(handle))

staging = []
with staging_path.open(newline='', encoding='utf-8') as handle:
    rows = csv.DictReader(handle, delimiter='\t')
    for row in rows:
        if not row.get('relativePath'):
            continue
        staging.append({
            'relativePath': row['relativePath'],
            'size': int(row['size']),
            'sha256': row['sha256'],
        })

counts = summary.get('counts', {})
def count(name):
    return int(counts.get(name, 0))

catalogued = len(plan.get('baselineRows', []))
matching = count('CATALOGUED_MATCH')
missing = count('DATABASE_ROW_MISSING_FILE')
untracked = count('CREATE_MISSING')
metadata = count('CATALOGUED_METADATA_CONFLICT')
unsupported = count('UNSUPPORTED')
untracked_physical = untracked + unsupported
staging_bytes = sum(item['size'] for item in staging)
requires_review = any((missing, untracked_physical, metadata, len(conflicts), len(staging)))

report = {
    'schemaVersion': 1,
    'feature': '0031-FEAT',
    'step': 9,
    'reconciliationType': 'pre-split-read-only',
    'createdAt': datetime.now(timezone.utc).isoformat(),
    'applicationSourceIdentity': {'gitCommit': source_identity},
    'logicalDataset': 'production',
    'configuredTargetFilesDir': 'files',
    'reconciledSharedFilesDir': 'files',
    'reconciledSharedFilesRoot': physical_root,
    'runtimeFilesRoot': summary.get('filesRoot'),
    'databaseIdentity': summary.get('databaseIdentity'),
    'reconciliationOutcome': summary.get('outcome'),
    'catalogue': {
        'imageRowCount': catalogued,
        'matchingPhysicalFiles': matching,
        'missingPhysicalFiles': missing,
        'untrackedPhysicalFiles': untracked_physical,
        'untrackedSupportedImageFiles': untracked,
        'metadataOrChecksumConflicts': metadata,
        'unsupportedPhysicalFiles': unsupported,
        'reconciliationConflictRows': len(conflicts),
        'statusCounts': counts,
    },
    'staging': {
        'runtimePath': '/data/files/.image-staging',
        'fileCount': len(staging),
        'totalBytes': staging_bytes,
        'inventoryFile': str(staging_path),
        'copiedOrModified': False,
    },
    'readOnly': True,
    'step10Ready': not requires_review,
    'requiresExplicitDisposition': requires_review,
    'evidence': {
        'directory': str(recon.parent),
        'reconciliationDirectory': str(recon),
        'summary': str(recon / '0024-summary.json'),
        'plan': str(recon / '0024-create-plan.json'),
        'conflicts': str(recon / '0024-conflicts.csv'),
        'stagingInventory': str(staging_path),
    },
}
report_json.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')

decision = 'REVIEW REQUIRED before Step 10' if requires_review else 'READY for Step 10'
report_md.write_text(f'''# 0031-FEAT Step 9 — production reconciliation report

- Dataset: `production`
- Database identity: `{summary.get("databaseIdentity", "")}`
- Shared Files root: `{physical_root}`
- Runtime Files root: `{summary.get("filesRoot", "")}`
- Reconciliation outcome: `{summary.get("outcome", "")}`
- Image rows: {catalogued}
- Matching physical files: {matching}
- Missing physical files: {missing}
- Untracked physical files: {untracked_physical}
- Untracked supported image files: {untracked}
- Unsupported physical files: {unsupported}
- Metadata/checksum conflicts: {metadata}
- Reconciliation conflict rows: {len(conflicts)}
- `.image-staging` files: {len(staging)}
- Decision: **{decision}**

This run is read-only. It does not apply the 0024 create plan, mutate Image rows,
or change Files bytes. Any non-zero anomaly above requires an explicit Step 9
disposition before Step 10 copies the shared tree.
''', encoding='utf-8')

print(f'Image rows:                  {catalogued}')
print(f'Matching physical files:     {matching}')
print(f'Missing physical files:      {missing}')
print(f'Untracked physical files:     {untracked_physical}')
print(f'Untracked supported images:  {untracked}')
print(f'Unsupported physical files:  {unsupported}')
print(f'Metadata/checksum conflicts: {metadata}')
print(f'Conflict rows:               {len(conflicts)}')
print(f'.image-staging files:        {len(staging)}')
print(f'Report:                      {report_json}')
print('RESULT: ' + decision)
PYREPORT

echo
echo "Step 9 production reconciliation captured."
echo "Keep both production and local responder write paths frozen."
echo "Do not proceed to Step 10 unless STEP9-REPORT.json says step10Ready=true or every reported exception has an explicit reviewed disposition."
