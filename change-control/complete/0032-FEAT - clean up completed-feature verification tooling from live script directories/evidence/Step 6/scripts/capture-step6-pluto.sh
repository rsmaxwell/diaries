#!/usr/bin/env bash
set -euo pipefail

PHASE="${1:-}"
PROJECT_DIR="${2:-/home/richard/projects/diaries}"
OUT_DIR="${3:-/tmp/0032-step6}"

case "${PHASE}" in
  pre|post) ;;
  *)
    echo "Usage: $0 pre|post [project-dir] [output-dir]" >&2
    exit 2
    ;;
esac

if [[ ! -d "${PROJECT_DIR}/scripts" ]]; then
  echo "ERROR: production scripts directory not found: ${PROJECT_DIR}/scripts" >&2
  exit 1
fi

mkdir -p "${OUT_DIR}"
HOST="$(hostname)"
CAPTURED="$(date --iso-8601=seconds)"
PHASE_UPPER="$(printf '%s' "${PHASE}" | tr '[:lower:]' '[:upper:]')"
INVENTORY="${OUT_DIR}/PLUTO-SCRIPTS-${PHASE_UPPER}.txt"
CONFIG="${OUT_DIR}/PRODUCTION-CONFIG-${PHASE_UPPER}.txt"

capture_inventory() {
  {
    echo "0032 Step 6 - pluto deployed scripts ${PHASE_UPPER}"
    echo "host: ${HOST}"
    echo "captured: ${CAPTURED}"
    echo "project: ${PROJECT_DIR}"
    echo
    printf 'TYPE\tMODE\tOWNER\tGROUP\tSIZE_BYTES\tSHA256\tPATH\n'
    cd "${PROJECT_DIR}"
    find scripts -maxdepth 1 -type f -print0 \
      | sort -z \
      | while IFS= read -r -d '' path; do
          printf 'FILE\t%s\t%s\t%s\t%s\t%s\t%s\n' \
            "$(stat -c '%a' "${path}")" \
            "$(stat -c '%U' "${path}")" \
            "$(stat -c '%G' "${path}")" \
            "$(stat -c '%s' "${path}")" \
            "$(sha256sum "${path}" | awk '{print $1}')" \
            "${path}"
        done
  } > "${INVENTORY}"
}

capture_config() {
  local required=(
    ".env"
    "compose.yaml"
    "config/responder/responder.json"
  )

  for rel in "${required[@]}"; do
    if [[ ! -f "${PROJECT_DIR}/${rel}" ]]; then
      echo "ERROR: required production configuration missing: ${PROJECT_DIR}/${rel}" >&2
      exit 1
    fi
  done

  {
    echo "0032 Step 6 - production configuration fingerprint ${PHASE_UPPER}"
    echo "host: ${HOST}"
    echo "captured: ${CAPTURED}"
    echo "project: ${PROJECT_DIR}"
    echo
    printf 'TYPE\tSHA256\tPATH\n'
    for rel in "${required[@]}"; do
      printf 'FILE\t%s\t%s\n' \
        "$(sha256sum "${PROJECT_DIR}/${rel}" | awk '{print $1}')" \
        "${rel}"
    done
    echo
    # Only non-secret selectors/contracts are emitted. The complete .env is never printed.
    grep -E '^DIARIES_(DB_NAME|FILES_DIR)=' "${PROJECT_DIR}/.env" \
      | sed 's/^/SELECTOR\t/' || true
    grep -F 'subpath: ${DIARIES_NAS_CONTENT_PATH}/${DIARIES_FILES_DIR}' "${PROJECT_DIR}/compose.yaml" \
      | sed 's/^[[:space:]]*/CONTRACT\tcompose.files\t/' || true
    grep -F 'diaries-db-data:/var/lib/postgresql' "${PROJECT_DIR}/compose.yaml" \
      | sed 's/^[[:space:]]*/CONTRACT\tcompose.database\t/' || true
    python3 - "${PROJECT_DIR}/config/responder/responder.json" <<'PY'
import json
import sys
from pathlib import Path
p = Path(sys.argv[1])
data = json.loads(p.read_text(encoding="utf-8"))
print(f"CONTRACT\tresponder.diaries.files\t{data.get('diaries', {}).get('files', '<missing>')}")
PY
  } > "${CONFIG}"
}

capture_status() {
  local status_file="${OUT_DIR}/PRODUCTION-STATUS.txt"
  local compose=(docker compose --file "${PROJECT_DIR}/compose.yaml" --env-file "${PROJECT_DIR}/.env")
  local required_services=(diaries-db diaries-mqtt diaries-responder diaries-client diaries-web)
  local failed=0

  {
    echo "0032 Step 6 - production status POST"
    echo "host: ${HOST}"
    echo "captured: ${CAPTURED}"
    echo "project: ${PROJECT_DIR}"
    echo

    echo '>>> docker compose config --quiet'
    if "${compose[@]}" config --quiet; then
      echo 'PASS: Docker Compose configuration is valid.'
    else
      echo 'FAIL: Docker Compose configuration is invalid.'
      failed=1
    fi

    echo
    echo '>>> normal Diaries status output'
    if "${PROJECT_DIR}/scripts/status.sh"; then
      echo 'PASS: scripts/status.sh completed successfully.'
    else
      echo 'FAIL: scripts/status.sh failed.'
      failed=1
    fi

    echo
    echo '>>> required service state / health'
    for service in "${required_services[@]}"; do
      cid="$("${compose[@]}" ps -q "${service}" 2>/dev/null || true)"
      if [[ -z "${cid}" ]]; then
        echo "FAIL: ${service}: no container id"
        failed=1
        continue
      fi
      state="$(docker inspect --format '{{.State.Status}}' "${cid}" 2>/dev/null || true)"
      health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "${cid}" 2>/dev/null || true)"
      echo "SERVICE: ${service} state=${state:-unknown} health=${health:-unknown}"
      if [[ "${state}" != "running" ]]; then
        echo "FAIL: ${service} is not running."
        failed=1
      elif [[ "${health}" != "healthy" ]]; then
        echo "FAIL: ${service} is not healthy."
        failed=1
      else
        echo "PASS: ${service} is running and healthy."
      fi
    done

    echo
    if [[ "${failed}" -eq 0 ]]; then
      echo 'PASS: Step 6 production health verification completed.'
    else
      echo 'FAIL: Step 6 production health verification found one or more problems.'
    fi
  } > "${status_file}" 2>&1

  return "${failed}"
}

capture_inventory
capture_config

if [[ "${PHASE}" == "post" ]]; then
  capture_status
fi

echo "Captured Step 6 ${PHASE} evidence in ${OUT_DIR}:"
echo "  ${INVENTORY}"
echo "  ${CONFIG}"
if [[ "${PHASE}" == "post" ]]; then
  echo "  ${OUT_DIR}/PRODUCTION-STATUS.txt"
fi
