#!/usr/bin/env bash
set -euo pipefail

fail() {
    echo "ERROR: 0031 Step 13: $*" >&2
    exit 1
}

usage() {
    cat >&2 <<'USAGE'
Usage:
  step13-capture-production-control.sh before
  step13-capture-production-control.sh after BEFORE_RUN_DIRECTORY

Captures the production Image table and a SHA-256 inventory of every mutable
Files file while diaries-responder is stopped. The after form requires the
before directory and fails if either durable control changed.
USAGE
    exit 2
}

[[ $# -ge 1 && $# -le 2 ]] || usage
PHASE="$1"
[[ "${PHASE}" == "before" || "${PHASE}" == "after" ]] || usage
if [[ "${PHASE}" == "before" ]]; then
    [[ $# -eq 1 ]] || usage
    BEFORE_RUN=""
else
    [[ $# -eq 2 ]] || usage
    BEFORE_RUN="$2"
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${PROJECT_DIR}/.env"
COMPOSE_FILE="${PROJECT_DIR}/compose.yaml"
[[ -f "${ENV_FILE}" ]] || fail "Environment file not found: ${ENV_FILE}"
[[ -f "${COMPOSE_FILE}" ]] || fail "Compose file not found: ${COMPOSE_FILE}"
command -v docker >/dev/null 2>&1 || fail "docker was not found on PATH"
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
[[ "${FILES_DIR}" == "files" ]] || fail "Production DIARIES_FILES_DIR must be 'files'; found '${FILES_DIR}'"
[[ -n "${CONTENT_PATH}" && -n "${DB_NAME}" && -n "${DB_USER}" ]] || fail "Required production environment values are missing"

COMPOSE=(docker compose --file "${COMPOSE_FILE}" --env-file "${ENV_FILE}")
cd -- "${PROJECT_DIR}"
"${COMPOSE[@]}" config --quiet
RUNNING="$("${COMPOSE[@]}" ps --status running --services)"
grep -Fxq 'diaries-db' <<<"${RUNNING}" || fail "Production database service diaries-db is not running"
if grep -Fxq 'diaries-responder' <<<"${RUNNING}"; then
    fail "Production responder is running. Step 13 production controls require the existing write freeze."
fi

if [[ -n "${BEFORE_RUN}" ]]; then
    [[ -d "${BEFORE_RUN}" ]] || fail "Before control directory does not exist: ${BEFORE_RUN}"
    BEFORE_RUN="$(cd -- "${BEFORE_RUN}" && pwd)"
    [[ -f "${BEFORE_RUN}/IMAGE-ROWS.tsv" && -f "${BEFORE_RUN}/FILES-INVENTORY.tsv" ]] || fail "Before control is incomplete: ${BEFORE_RUN}"
fi

TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
RUN_DIR="${PROJECT_DIR}/data/0031-step13/production-${PHASE}-${TIMESTAMP}"
mkdir -p -- "${RUN_DIR}"

IMAGE_ROWS="${RUN_DIR}/IMAGE-ROWS.tsv"
FILES_INVENTORY="${RUN_DIR}/FILES-INVENTORY.tsv"
CONTROL="${RUN_DIR}/CONTROL.txt"

"${COMPOSE[@]}" exec -T diaries-db psql -X -v ON_ERROR_STOP=1 -U "${DB_USER}" -d "${DB_NAME}" \
    -c "COPY (SELECT id,version,relative_path,mime_type,original_filename,width,height,checksum,caption,alt_text FROM public.image ORDER BY id) TO STDOUT WITH (FORMAT csv, HEADER true, DELIMITER E'\\t');" \
    > "${IMAGE_ROWS}"

# Read-only disposable shell over the production /data/files mount. The sort is
# deterministic and the inventory includes .image-staging if it exists.
"${COMPOSE[@]}" run --rm --no-deps --no-tty --pull never --entrypoint sh diaries-responder -c '
set -eu
find /data/files -type f -print | LC_ALL=C sort | while IFS= read -r file; do
  rel=${file#/data/files/}
  bytes=$(wc -c < "$file" | tr -d " ")
  hash_line=$(sha256sum "$file")
  hash=${hash_line%% *}
  printf "%s\t%s\t%s\n" "$rel" "$bytes" "$hash"
done
' > "${FILES_INVENTORY}"

IMAGE_HASH="$(sha256sum "${IMAGE_ROWS}" | awk '{print $1}')"
FILES_HASH="$(sha256sum "${FILES_INVENTORY}" | awk '{print $1}')"
IMAGE_COUNT="$(( $(wc -l < "${IMAGE_ROWS}") - 1 ))"
FILES_COUNT="$(wc -l < "${FILES_INVENTORY}")"
PHYSICAL_SUBPATH="${CONTENT_PATH%/}/${FILES_DIR}"
cat > "${CONTROL}" <<CONTROL
feature=0031-FEAT
step=13
phase=${PHASE}
capturedAt=$(date --iso-8601=seconds)
effectiveFilesDir=${FILES_DIR}
physicalNasSubpath=${PHYSICAL_SUBPATH}
imageRowCount=${IMAGE_COUNT}
imageRowsSha256=${IMAGE_HASH}
filesFileCount=${FILES_COUNT}
filesInventorySha256=${FILES_HASH}
productionResponderRunning=false
CONTROL

if [[ "${PHASE}" == "after" ]]; then
    if ! cmp -s -- "${BEFORE_RUN}/IMAGE-ROWS.tsv" "${IMAGE_ROWS}"; then
        fail "Production Image catalogue changed during the Step 13 local lifecycle. Compare ${BEFORE_RUN}/IMAGE-ROWS.tsv with ${IMAGE_ROWS}"
    fi
    if ! cmp -s -- "${BEFORE_RUN}/FILES-INVENTORY.tsv" "${FILES_INVENTORY}"; then
        fail "Production mutable Files tree changed during the Step 13 local lifecycle. Compare ${BEFORE_RUN}/FILES-INVENTORY.tsv with ${FILES_INVENTORY}"
    fi
    cat > "${RUN_DIR}/COMPARISON.txt" <<COMPARE
PASS: production Image rows are byte-for-byte identical to the Step 13 BEFORE control.
PASS: production mutable Files SHA-256 inventory is byte-for-byte identical to the Step 13 BEFORE control.
before=${BEFORE_RUN}
after=${RUN_DIR}
COMPARE
    echo "PASS: Step 13 production controls are unchanged."
    echo "Comparison: ${RUN_DIR}/COMPARISON.txt"
else
    echo "PASS: Step 13 production BEFORE control captured with responder writes frozen."
fi

echo "Evidence: ${RUN_DIR}"
