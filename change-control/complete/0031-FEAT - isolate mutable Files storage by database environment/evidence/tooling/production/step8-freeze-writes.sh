#!/usr/bin/env bash

set -euo pipefail

# 0031-FEAT Step 8: freeze production mutable Image/File writes without
# stopping PostgreSQL. The responder owns all catalogue Files mutations, so
# stopping only that service preserves database availability for pg_dump.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_FILE="${PROJECT_DIR}/compose.yaml"
ENV_FILE="${PROJECT_DIR}/.env"
RESPONDER_SERVICE="${DIARIES_RESPONDER_SERVICE:-diaries-responder}"
EVIDENCE_DIR="${PROJECT_DIR}/data/0031-step8"
TIMESTAMP="$(date '+%Y%m%d-%H%M%S')"
EVIDENCE_FILE="${EVIDENCE_DIR}/production-write-freeze-${TIMESTAMP}.txt"

require_file() {
    local path="$1"
    local description="$2"
    if [[ ! -f "${path}" ]]; then
        echo "ERROR: ${description} not found: ${path}" >&2
        exit 1
    fi
}

require_file "${COMPOSE_FILE}" "Diaries Compose file"
require_file "${ENV_FILE}" "Diaries environment file"
mkdir -p "${EVIDENCE_DIR}"

exec > >(tee -a "${EVIDENCE_FILE}") 2>&1

echo "0031-FEAT Step 8 - production mutable-write freeze"
echo "Captured: $(date --iso-8601=seconds)"
echo "Host: $(hostname)"
echo "Project: ${PROJECT_DIR}"
echo

cd "${PROJECT_DIR}"
docker compose --file "${COMPOSE_FILE}" --env-file "${ENV_FILE}" config --quiet

if docker compose --file "${COMPOSE_FILE}" --env-file "${ENV_FILE}" ps --status running --services | grep -Fxq "${RESPONDER_SERVICE}"; then
    echo "Stopping production responder service: ${RESPONDER_SERVICE}"
    docker compose --file "${COMPOSE_FILE}" --env-file "${ENV_FILE}" stop "${RESPONDER_SERVICE}"
else
    echo "Production responder service already stopped/not running: ${RESPONDER_SERVICE}"
fi

if docker compose --file "${COMPOSE_FILE}" --env-file "${ENV_FILE}" ps --status running --services | grep -Fxq "${RESPONDER_SERVICE}"; then
    echo "ERROR: responder service is still running; mutable-write freeze is not proven." >&2
    exit 1
fi

DB_SERVICE="${DIARIES_DB_SERVICE:-diaries-db}"
if ! docker compose --file "${COMPOSE_FILE}" --env-file "${ENV_FILE}" ps --status running --services | grep -Fxq "${DB_SERVICE}"; then
    echo "ERROR: database service '${DB_SERVICE}' is not running. Leave the responder stopped and restore database availability before capture." >&2
    exit 1
fi

SOURCE_IDENTITY="unknown"
if command -v git >/dev/null 2>&1 && git -C "${PROJECT_DIR}" rev-parse HEAD >/dev/null 2>&1; then
    SOURCE_IDENTITY="$(git -C "${PROJECT_DIR}" rev-parse HEAD)"
fi

echo
echo "PASS: production responder is stopped."
echo "PASS: production database remains running for backup."
echo "Playbooks/runtime source identity: ${SOURCE_IDENTITY}"
echo "Production mutable Image/File writes are frozen."
echo "Leave the responder stopped until the 0031 migration sequence says it is safe to restart."
echo "Evidence: ${EVIDENCE_FILE}"
