#!/usr/bin/env bash
set -euo pipefail

fail() {
    echo "ERROR: 0031 Step 12: $*" >&2
    exit 1
}

usage() {
    cat >&2 <<'EOF'
Usage: step12-reconcile-production.sh --write-freeze-confirmed [STEP9_RUN]

Runs the existing 0024 Image reconciliation in dry-run mode against the deployed
production database + Files pair, then compares the semantic result with the
Step 9 pre-split production baseline.
EOF
    exit 2
}

[[ $# -ge 1 && $# -le 2 ]] || usage
[[ "$1" == "--write-freeze-confirmed" ]] || usage
STEP9_OVERRIDE="${2:-}"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${PROJECT_DIR}/.env"
COMPOSE_FILE="${PROJECT_DIR}/compose.yaml"
MIGRATION="${SCRIPT_DIR}/migration0024ImageCatalogue.sh"
COMPARATOR="${SCRIPT_DIR}/step12-compare-reconciliation.py"

[[ -f "${ENV_FILE}" ]] || fail "Environment file not found: ${ENV_FILE}"
[[ -f "${COMPOSE_FILE}" ]] || fail "Compose file not found: ${COMPOSE_FILE}"
[[ -x "${MIGRATION}" ]] || fail "Existing 0024 migration helper not found/executable: ${MIGRATION}"
[[ -f "${COMPARATOR}" ]] || fail "Step 12 comparator not found: ${COMPARATOR}"
command -v docker >/dev/null 2>&1 || fail "docker was not found on PATH"
command -v python3 >/dev/null 2>&1 || fail "python3 was not found on PATH"

read_env_value() {
    local key="$1"
    local line
    line="$(grep -E "^[[:space:]]*${key}=" "${ENV_FILE}" | tail -n 1 || true)"
    [[ -n "${line}" ]] || return 1
    local value="${line#*=}"
    value="${value%$'\r'}"
    if [[ "${value}" == \"*\" && "${value}" == *\" ]]; then value="${value:1:${#value}-2}"; fi
    if [[ "${value}" == \'*\' && "${value}" == *\' ]]; then value="${value:1:${#value}-2}"; fi
    printf '%s' "${value}"
}

FILES_DIR="$(read_env_value DIARIES_FILES_DIR || true)"
CONTENT_PATH="$(read_env_value DIARIES_NAS_CONTENT_PATH || true)"
[[ "${FILES_DIR}" == "files" ]] || fail "Production DIARIES_FILES_DIR must be 'files'; found '${FILES_DIR}'"
[[ -n "${CONTENT_PATH}" ]] || fail "DIARIES_NAS_CONTENT_PATH is missing from ${ENV_FILE}"

COMPOSE=(docker compose --file "${COMPOSE_FILE}" --env-file "${ENV_FILE}")
cd -- "${PROJECT_DIR}"
"${COMPOSE[@]}" config --quiet

RUNNING="$("${COMPOSE[@]}" ps --status running --services)"
grep -Fxq 'diaries-db' <<<"${RUNNING}" || fail "Production database service diaries-db is not running"
if grep -Fxq 'diaries-responder' <<<"${RUNNING}"; then
    fail "Production responder is running. Keep the Step 8/12 write freeze in force and stop diaries-responder before this reconciliation."
fi

STEP9_ROOT="${PROJECT_DIR}/data/0031-step9"
if [[ -n "${STEP9_OVERRIDE}" ]]; then
    [[ -d "${STEP9_OVERRIDE}" ]] || fail "Specified Step 9 run does not exist: ${STEP9_OVERRIDE}"
    STEP9_RUN="$(cd -- "${STEP9_OVERRIDE}" && pwd)"
else
    [[ -d "${STEP9_ROOT}" ]] || fail "Step 9 evidence root not found: ${STEP9_ROOT}"
    STEP9_RUN="$(find "${STEP9_ROOT}" -mindepth 1 -maxdepth 1 -type d -name 'production-*' -print | sort -r | head -n 1)"
    [[ -n "${STEP9_RUN}" ]] || fail "No production-* Step 9 baseline found under ${STEP9_ROOT}"
fi

TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
RUN_DIR="${PROJECT_DIR}/data/0031-step12/production-${TIMESTAMP}"
RUNNER_ROOT="${RUN_DIR}/migration-runner"
mkdir -p -- "${RUN_DIR}" "${RUNNER_ROOT}"

PHYSICAL_SUBPATH="${CONTENT_PATH%/}/${FILES_DIR}"
python3 - "${RUN_DIR}/PAIR.json" "${PHYSICAL_SUBPATH}" "${STEP9_RUN}" <<'PY'
import json, sys
from datetime import datetime, timezone
out, physical, baseline = sys.argv[1:]
value = {
    "schemaVersion": 1,
    "feature": "0031-FEAT",
    "step": 12,
    "dataset": "production",
    "effectiveFilesDir": "files",
    "effectiveDbDataDir": "production-compose-database",
    "physicalNasSubpath": physical,
    "dockerFilesRoot": "/data/files",
    "publicFilesRoute": "/files/...",
    "step9BaselineRun": baseline,
    "productionWriteFreezeConfirmed": True,
    "capturedAt": datetime.now(timezone.utc).isoformat(),
}
with open(out, "w", encoding="utf-8") as handle:
    json.dump(value, handle, indent=2)
    handle.write("\n")
PY

STAGING="${RUN_DIR}/STAGING-INVENTORY.tsv"
printf 'relativePath\titemType\tsize\tmtime\n' > "${STAGING}"
set +e
"${COMPOSE[@]}" run --rm --no-deps --no-tty --pull never --entrypoint sh diaries-responder -c '
root=/data/files/.image-staging
if [ -d "$root" ]; then
  find "$root" -mindepth 1 -print | sort | while IFS= read -r p; do
    rel=${p#"$root"/}
    if [ -d "$p" ]; then kind=directory; size=0; else kind=file; size=$(wc -c < "$p" 2>/dev/null || echo unknown); fi
    printf "%s\t%s\t%s\t%s\n" "$rel" "$kind" "$size" "unrecorded"
  done
fi
' >> "${STAGING}" 2>"${RUN_DIR}/staging-inventory.stderr"
STAGING_RC=$?
set -e
if [[ ${STAGING_RC} -ne 0 ]]; then
    printf 'UNAVAILABLE\tprobe-failed\t0\tunrecorded\n' >> "${STAGING}"
fi

echo "Running production 0024 dry-run reconciliation..."
echo "  Step 9 baseline : ${STEP9_RUN}"
echo "  Files selector  : ${FILES_DIR}"
echo "  NAS subpath     : ${PHYSICAL_SUBPATH}"
echo "  evidence        : ${RUN_DIR}"

export DIARIES_MIGRATION0024_EVIDENCE_ROOT="${RUNNER_ROOT}"
if "${MIGRATION}" dry-run 2>&1 | tee "${RUN_DIR}/reconciliation-console.txt"; then
    :
else
    rc=${PIPESTATUS[0]}
    fail "0024 production dry-run failed with exit code ${rc}; evidence remains in ${RUN_DIR}"
fi

[[ -d "${RUNNER_ROOT}/dry-run" ]] || fail "Migration helper did not produce ${RUNNER_ROOT}/dry-run"
mv -- "${RUNNER_ROOT}/dry-run" "${RUN_DIR}/reconciliation"
rmdir "${RUNNER_ROOT}/apply" 2>/dev/null || true
rmdir "${RUNNER_ROOT}" 2>/dev/null || true

for required in 0024-summary.json 0024-file-inventory.csv 0024-conflicts.csv SHA256SUMS.txt; do
    [[ -f "${RUN_DIR}/reconciliation/${required}" ]] || fail "Missing reconciliation evidence: ${required}"
done

python3 "${COMPARATOR}" \
    --dataset production \
    --baseline "${STEP9_RUN}" \
    --current "${RUN_DIR}" \
    --expected-files-dir files \
    --expect-files-root same \
    --output-prefix "${RUN_DIR}/STEP12-REPORT"

echo "PASS: Step 12 production reconciliation matches the Step 9 semantic baseline."
echo "Evidence: ${RUN_DIR}"
echo "Copy/preserve this complete production-* directory with the Diaries Step 12 evidence before close-out."
