#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 /path/to/playbooks" >&2
    exit 2
fi

PLAYBOOKS_ROOT="$(cd "$1" && pwd)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH="${SCRIPT_DIR}/playbooks-0032-step5.patch"

[[ -f "${PLAYBOOKS_ROOT}/roles/diaries/tasks/copy.yaml" ]] || {
    echo "ERROR: not a Playbooks root: ${PLAYBOOKS_ROOT}" >&2
    exit 1
}

cd "${PLAYBOOKS_ROOT}"

if [[ -f roles/diaries/tests/verify-production-deployment-contract.py \
   && ! -e roles/diaries/files/sync/scripts/step14-production-deployment.sh \
   && ! -e roles/diaries/tests/verify-0031-step14.py ]]; then
    echo "Step 5 source patch appears to be already applied; running validation only."
else
    git apply --check "${PATCH}"
    git apply "${PATCH}"
    echo "Applied Step 5 Playbooks source patch."
fi

python roles/diaries/tests/verify-production-backup-restore-semantics.py
python roles/diaries/tests/verify-production-storage-isolation.py
python roles/diaries/tests/verify-production-deployment-contract.py

echo
echo "PASS: Step 5 Playbooks source application and validation completed."
echo "No playbook deployment has been run by this script."
