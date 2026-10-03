#!/usr/bin/env bash
set -euo pipefail

PLAYBOOKS_ROOT="${1:-$(pwd)}"
LOG="${2:-/tmp/0032-step8-playbooks-host-regression.txt}"

cd "$PLAYBOOKS_ROOT"
exec > >(tee "$LOG") 2>&1

run() {
    echo
    echo "=== $1 ==="
    shift
    "$@"
}

run "Production storage isolation" python3 roles/diaries/tests/verify-production-storage-isolation.py
run "Production backup/restore semantics" python3 roles/diaries/tests/verify-production-backup-restore-semantics.py
run "Production deployment/managed-scripts contract" python3 roles/diaries/tests/verify-production-deployment-contract.py
run "Ansible diaries.yaml syntax check" ansible-playbook --syntax-check diaries.yaml --vault-password-file "$HOME/.vault_pass.txt"

echo
echo "PASS: Playbooks Step 8 host regression completed successfully."
echo "Evidence: $LOG"
