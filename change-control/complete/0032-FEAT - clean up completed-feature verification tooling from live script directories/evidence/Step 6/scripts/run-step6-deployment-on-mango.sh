#!/usr/bin/env bash
set -euo pipefail

PLAYBOOK_DIR="${1:-/home/richard/playbooks}"
OUT_DIR="${2:-/tmp/0032-step6}"
mkdir -p "${OUT_DIR}"

cd "${PLAYBOOK_DIR}"

required=(
  roles/diaries/tests/verify-production-backup-restore-semantics.py
  roles/diaries/tests/verify-production-storage-isolation.py
  roles/diaries/tests/verify-production-deployment-contract.py
  scripts/diaries.sh
)
for path in "${required[@]}"; do
  if [[ ! -f "${path}" ]]; then
    echo "ERROR: required Playbooks file missing: ${PLAYBOOK_DIR}/${path}" >&2
    exit 1
  fi
done

if ! grep -Eq -- '--tags([ =]+)copy([[:space:]]|$)' scripts/diaries.sh; then
  echo "ERROR: scripts/diaries.sh is not currently restricted to the copy tag." >&2
  echo "Refusing to run a broader production play from the Step 6 wrapper." >&2
  exit 1
fi

VALIDATION_OUT="${OUT_DIR}/PLAYBOOK-SOURCE-VALIDATION.txt"
PLAYBOOK_OUT="${OUT_DIR}/PLAYBOOK-OUTPUT.txt"

{
  echo '0032 Step 6 - Playbooks source pre-deployment validation'
  echo "host: $(hostname)"
  echo "captured: $(date --iso-8601=seconds)"
  echo "playbooks: ${PLAYBOOK_DIR}"
  echo
  python3 roles/diaries/tests/verify-production-backup-restore-semantics.py
  python3 roles/diaries/tests/verify-production-storage-isolation.py
  python3 roles/diaries/tests/verify-production-deployment-contract.py
  echo
  echo 'PASS: Step 6 Playbooks source pre-deployment validation completed.'
} 2>&1 | tee "${VALIDATION_OUT}"

{
  echo '0032 Step 6 - controlled Diaries deployment'
  echo "host: $(hostname)"
  echo "started: $(date --iso-8601=seconds)"
  echo "playbooks: ${PLAYBOOK_DIR}"
  echo 'command: ./scripts/diaries.sh'
  echo
  ./scripts/diaries.sh
  rc=$?
  echo
  echo "finished: $(date --iso-8601=seconds)"
  echo "exit_code: ${rc}"
  exit "${rc}"
} 2>&1 | tee "${PLAYBOOK_OUT}"

echo "Step 6 deployment output written to: ${PLAYBOOK_OUT}"
