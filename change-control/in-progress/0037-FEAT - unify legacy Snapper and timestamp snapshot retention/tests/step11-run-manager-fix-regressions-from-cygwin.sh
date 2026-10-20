#!/usr/bin/env bash
set -euo pipefail
cd /cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries
feature='change-control/in-progress/0037-FEAT - unify legacy Snapper and timestamp snapshot retention'
manager='/home/richard/playbooks/roles/snapshots/files/btrfs-snapshot-manager.py'
mkdir -p "$feature/evidence/Step 11/manager-fix"
{
  ssh mango "python3 -m py_compile '$manager' && sha256sum '$manager'"
  ssh mango "python3 - '$manager'" < "$feature/tests/step11-snapper-fast-inventory-regression.py"
  ssh mango 'cd /home/richard/playbooks && python3 roles/snapshots/tests/verify-btrfs-snapshot-manager.py'
  bash "$feature/tests/step07-run-from-cygwin.sh"
} 2>&1 | tee "$feature/evidence/Step 11/manager-fix/regression-results.txt"
