#!/usr/bin/env bash
# Run non-interactively ON mango through ssh mango 'bash -s' < this-file.
# No host accounts, sudoers, SSH files, root state, timers or snapshots modified.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

cd /home/richard/ansible-controller
printf '0041 SOURCE CANDIDATE CHECK: %s UTC on %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$(hostname)"

printf '\n=== Controller repository and submodules ===\n'
test "$(git rev-parse HEAD)" = 83cba342d9ffe7da51a97bda9231f32d02beb2e3
printf 'controller=%s\n' "$(git rev-parse HEAD)"
git submodule status

cd playbooks
test "$(git rev-parse HEAD)" = c5109340a2fe13296a2343c682e1079d1a212c8d
printf 'playbooks=%s\n' "$(git rev-parse HEAD)"

printf '\n=== Review exact working-tree changes ===\n'
git status --short
if [ -n "$(git diff --cached --name-only)" ]; then
  echo 'FAIL: staged Playbooks changes exist' >&2
  exit 1
fi
# These are candidate-only modifications; any other working-tree changes
# would invalidate the review boundary.
if git status --porcelain --untracked-files=all | sed -E 's/^...//' | grep -Ev '^roles/btrfs-replication/' ; then
  echo 'FAIL: changes outside btrfs-replication detected' >&2
  exit 1
fi

git diff --check
python3 roles/btrfs-replication/tests/verify-0041-restricted-identity.py
python3 roles/btrfs-replication/tests/verify-replication.py
printf '\n=== Verify Python/Bash/YAML sources ===\n'
python3 - <<'PY'
import ast
from pathlib import Path
import yaml
role=Path('roles/btrfs-replication')
for path in [*role.glob('files/*.py'),*role.glob('tests/verify-0041-*.py')]:
    ast.parse(path.read_text(),filename=str(path))
for path in (role/'tasks/service-identities-0041.yaml',role/'tasks/native.yaml',role/'defaults/main.yaml'):
    yaml.safe_load(path.read_text())
print('PASS: Python AST and candidate YAML')
PY
bash -n roles/btrfs-replication/files/btrfs-replication-sender-cycle-0041.sh

printf '\n=== Active Ansible environment and syntax ===\n'
source /home/richard/ansible-controller/enter.sh
ansible-playbook btrfs-replication.yaml --syntax-check --vault-password-file ~/.vault_pass.txt

printf '\n=== Read-only, deliberately partial first-run preview ===\n'
ansible-playbook btrfs-replication.yaml --check --diff \
  --limit 'mars,backup' --tags btrfs-0041-provision \
  -e btrfs_0041_additive_enabled=true \
  --vault-password-file ~/.vault_pass.txt

printf '\nPASS: 0041 source and check-mode candidate evaluated; no live provisioning\n'
