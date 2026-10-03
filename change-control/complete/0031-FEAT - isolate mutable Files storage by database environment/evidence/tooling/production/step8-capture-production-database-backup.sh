#!/usr/bin/env bash

set -euo pipefail

# 0031-FEAT Step 8: take the production pre-migration PostgreSQL backup after
# mutable writes have been frozen. This deliberately remains database-only;
# the one shared pre-split Files snapshot is captured separately from Windows
# after both local and production responders are confirmed stopped.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_FILE="${PROJECT_DIR}/compose.yaml"
ENV_FILE="${PROJECT_DIR}/.env"
RESPONDER_SERVICE="${DIARIES_RESPONDER_SERVICE:-diaries-responder}"
DB_SERVICE="${DIARIES_DB_SERVICE:-diaries-db}"
BACKUP_SCRIPT="${SCRIPT_DIR}/backup-db-to-binary.sh"
EVIDENCE_DIR="${PROJECT_DIR}/data/0031-step8"
TIMESTAMP="$(date '+%Y%m%d-%H%M%S')"
EVIDENCE_FILE="${EVIDENCE_DIR}/production-database-backup-${TIMESTAMP}.txt"
STEP8_MANIFEST="${EVIDENCE_DIR}/production-database-backup-${TIMESTAMP}.json"

for path in "${COMPOSE_FILE}" "${ENV_FILE}" "${BACKUP_SCRIPT}"; do
    if [[ ! -f "${path}" ]]; then
        echo "ERROR: required file not found: ${path}" >&2
        exit 1
    fi
done
if [[ ! -x "${BACKUP_SCRIPT}" ]]; then
    echo "ERROR: database backup helper is not executable: ${BACKUP_SCRIPT}" >&2
    exit 1
fi
mkdir -p "${EVIDENCE_DIR}"

exec > >(tee -a "${EVIDENCE_FILE}") 2>&1

echo "0031-FEAT Step 8 - production pre-migration database backup"
echo "Captured: $(date --iso-8601=seconds)"
echo "Host: $(hostname)"
echo "Project: ${PROJECT_DIR}"
echo

cd "${PROJECT_DIR}"
docker compose --file "${COMPOSE_FILE}" --env-file "${ENV_FILE}" config --quiet

if docker compose --file "${COMPOSE_FILE}" --env-file "${ENV_FILE}" ps --status running --services | grep -Fxq "${RESPONDER_SERVICE}"; then
    echo "ERROR: responder service '${RESPONDER_SERVICE}' is running." >&2
    echo "Run ${SCRIPT_DIR}/step8-freeze-writes.sh first." >&2
    exit 1
fi
if ! docker compose --file "${COMPOSE_FILE}" --env-file "${ENV_FILE}" ps --status running --services | grep -Fxq "${DB_SERVICE}"; then
    echo "ERROR: database service '${DB_SERVICE}' is not running." >&2
    exit 1
fi

# Step 2 freezes production on the existing pre-split directory named "files".
# Refuse an unexpected selector so this capture cannot silently bless the wrong
# production/source Files identity.
PRODUCTION_FILES_DIR="$(python3 - "${ENV_FILE}" <<'PY'
import sys
from pathlib import Path
value = None
for raw in Path(sys.argv[1]).read_text(encoding='utf-8').splitlines():
    line = raw.strip()
    if not line or line.startswith('#') or '=' not in raw:
        continue
    key, val = raw.split('=', 1)
    if key.strip() == 'DIARIES_FILES_DIR':
        value = val.strip()
        break
print(value or '')
PY
)"
if [[ "${PRODUCTION_FILES_DIR}" != "files" ]]; then
    echo "ERROR: production DIARIES_FILES_DIR is '${PRODUCTION_FILES_DIR}', expected frozen Step-2 value 'files'." >&2
    exit 1
fi

DB_LOG="${EVIDENCE_DIR}/production-database-backup-helper-${TIMESTAMP}.txt"
"${BACKUP_SCRIPT}" 2>&1 | tee "${DB_LOG}"

DB_MANIFEST="$(sed -n 's/^Manifest: //p' "${DB_LOG}" | tail -n 1)"
if [[ -z "${DB_MANIFEST}" || ! -s "${DB_MANIFEST}" ]]; then
    echo "ERROR: unable to locate the Step-7 database sidecar from backup output." >&2
    exit 1
fi
DB_BACKUP="${DB_MANIFEST%.dataset.json}"
if [[ ! -s "${DB_BACKUP}" ]]; then
    echo "ERROR: database backup file referenced by sidecar is missing/empty: ${DB_BACKUP}" >&2
    exit 1
fi

DB_SHA256="$(sha256sum "${DB_BACKUP}" | awk '{print $1}')"
SIDECAR_SHA256="$(sha256sum "${DB_MANIFEST}" | awk '{print $1}')"
RUNTIME_IMAGES="$(docker compose --file "${COMPOSE_FILE}" --env-file "${ENV_FILE}" config --images 2>/dev/null || true)"
SOURCE_IDENTITY="unknown"
if command -v git >/dev/null 2>&1 && git -C "${PROJECT_DIR}" rev-parse HEAD >/dev/null 2>&1; then
    SOURCE_IDENTITY="$(git -C "${PROJECT_DIR}" rev-parse HEAD)"
fi

python3 - "${STEP8_MANIFEST}" "${DB_BACKUP}" "${DB_SHA256}" "${DB_MANIFEST}" "${SIDECAR_SHA256}" "${SOURCE_IDENTITY}" "${RUNTIME_IMAGES}" <<'PY'
import json
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path

out, backup, backup_sha, sidecar, sidecar_sha, source_identity, runtime_images = sys.argv[1:]
manifest = {
    'schemaVersion': 1,
    'captureType': '0031-step8-production-pre-migration-database',
    'createdAt': datetime.now(timezone.utc).astimezone().isoformat(),
    'host': socket.gethostname(),
    'logicalDataset': 'production',
    'databaseStorage': 'diaries-db-data',
    'preMigrationSharedFilesDir': 'files',
    'databaseBackupFile': backup,
    'databaseBackupSha256': backup_sha,
    'databaseSidecarFile': sidecar,
    'databaseSidecarSha256': sidecar_sha,
    'writeFreeze': {'productionResponderStopped': True},
    'applicationSourceIdentity': {
        'playbooksGitCommit': source_identity,
        'runtimeImages': [line for line in runtime_images.splitlines() if line.strip()],
    },
    'note': 'Production database backup captured while responder writes were frozen. Pair it with the single Step-8 snapshot of the pre-split shared Files root.',
}
Path(out).write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
PY

echo
echo "PASS: production pre-migration database backup captured and hashed."
echo "Database backup: ${DB_BACKUP}"
echo "Database SHA-256: ${DB_SHA256}"
echo "Step-7 sidecar: ${DB_MANIFEST}"
echo "Step-8 manifest: ${STEP8_MANIFEST}"
echo "The shared Files bytes are captured separately after local and production freezes are both established."
