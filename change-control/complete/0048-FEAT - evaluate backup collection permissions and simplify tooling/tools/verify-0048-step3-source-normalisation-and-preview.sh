#!/usr/bin/env bash
# 0048-FEAT: verify exact candidate, normalise local Playbooks source metadata,
# then preview the selected backup-collection tasks on mars. Does NOT deploy.
set -euo pipefail

controller=/home/richard/ansible-controller
playbooks="$controller/playbooks"
role="$playbooks/roles/backup-collection"

printf '%s\n' '0048 STEP 3: SOURCE NORMALISATION AND CHECK-MODE DEPLOYMENT PREVIEW'
printf 'UTC: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'HOST: %s\n' "$(hostname)"

cd "$controller"
test "$(git rev-parse HEAD)" = 'f6ba7fec7752f4bbfa1535958500bde9dea3ea84' || {
  echo 'FAIL: Ansible controller commit has changed; inspect before proceeding' >&2
  exit 1
}
test "$(git rev-parse HEAD:playbooks)" = 'df68a0e3bc57bae29a76f46a58c30835126d7f20' || {
  echo 'FAIL: parent no longer pins the reviewed Playbooks revision' >&2
  exit 1
}
test "$(git -C inventory rev-parse HEAD)" = 'ebcce026723db37b9b53b76ba21903a351d48466' || {
  echo 'FAIL: inventory revision has changed; inspect before proceeding' >&2
  exit 1
}
cd "$playbooks"
test "$(git rev-parse HEAD)" = 'df68a0e3bc57bae29a76f46a58c30835126d7f20' || {
  echo 'FAIL: Playbooks checkout commit has changed; inspect before proceeding' >&2
  exit 1
}
git diff --cached --quiet || { echo 'FAIL: staged changes in Playbooks' >&2; exit 1; }
git diff --check || { echo 'FAIL: whitespace/error in Playbooks diff' >&2; exit 1; }

printf '%s\n' '=== Candidate tracked changes (read-only review) ==='
git status --short
git diff --stat
actual_diff="$(git diff --name-only | LC_ALL=C sort)"
expected_diff="$(printf '%s\n' \
 'roles/backup-collection/README.md' \
 'roles/backup-collection/tasks/install_user_scripts.yaml' \
 'roles/backup-collection/tests/verify-collection-source-modes.py' | LC_ALL=C sort)"
if [[ "$actual_diff" != "$expected_diff" ]]; then
  printf 'FAIL: tracked changes differ from reviewed candidate:\n%s\n' "$actual_diff" >&2
  exit 1
fi

# Exact candidate-file verification prevents testing an accidental hybrid patch.
python3 - "$role" <<'PYVERIFY'
import hashlib, pathlib, sys
role = pathlib.Path(sys.argv[1])
expected = {
 'README.md': '433f788921513edcbf8302205c22383e4b2b794af125732b0d13c5a096976cc0',
 'tasks/install_machine_scripts.yaml': 'b2e2de704c976d7dad3b0a2216ee53c006620902f1e9a2ebe43d0420ddfaaf4c',
 'tasks/install_user_scripts.yaml': '1c27006c86c6f4f89a549bf2a17494363965b2a39460b9d57fe680a8e4d56b48',
 'tests/verify-collection-source-modes.py': 'a865218d29f8ef5f3fdd11062ea595539871f19197fbf703796880a0fff8053d',
}
for name, digest in expected.items():
 p = role / name
 if not p.is_file() or p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest() != digest:
  raise SystemExit(f'FAIL: candidate source differs: {name}')
print('PASS: exact previously reviewed candidate source files')
PYVERIFY

sources=(
  "$role/files/backup"
  "$role/files/backup/home"
  "$role/files/backup-machine"
  "$role/files/backup-machine/home"
  "$role/files/backup-machine/remote"
)
filters=(
  "$role/files/backup/home/includes"
  "$role/files/backup/home/excludes-1"
  "$role/files/backup/home/excludes-2"
  "$role/files/backup-machine/home/includes"
  "$role/files/backup-machine/home/excludes-1"
  "$role/files/backup-machine/home/excludes-2"
  "$role/files/backup-machine/remote/includes"
  "$role/files/backup-machine/remote/excludes-1"
  "$role/files/backup-machine/remote/excludes-2"
)
for path in "${sources[@]}"; do
  [[ -d "$path" && ! -L "$path" ]] || { echo "FAIL: unexpected directory $path" >&2; exit 1; }
done
for path in "${filters[@]}"; do
  [[ -f "$path" && ! -L "$path" ]] || { echo "FAIL: unexpected file $path" >&2; exit 1; }
done

printf '%s\n' '=== Before local checkout mode normalisation ==='
stat -c '%a %U:%G %n' "${sources[@]}" "${filters[@]}"

# Only these 14 working-copy metadata entries are changed; no contents, Git
# commits, deployed files, backup datasets, schedules or snapshots are touched.
chmod 0755 -- "${sources[@]}"
chmod 0644 -- "${filters[@]}"

printf '%s\n' '=== After local checkout mode normalisation ==='
stat -c '%a %U:%G %n' "${sources[@]}" "${filters[@]}"

printf '%s\n' '=== Revised source-mode preflight and hash validation ==='
python3 "$role/tests/verify-collection-source-modes.py"

export ANSIBLE_CONFIG=/etc/ansible/ansible.cfg
export ANSIBLE_INVENTORY="$controller/inventory/hosts"
test -f "$ANSIBLE_INVENTORY" || { echo 'FAIL: post-0046 inventory missing' >&2; exit 1; }
test -f "$HOME/.vault_pass.txt" || { echo 'FAIL: vault password file missing' >&2; exit 1; }

printf '%s\n' '=== Ansible syntax check ==='
ansible-playbook backup-collection.yaml \
  --syntax-check --vault-password-file "$HOME/.vault_pass.txt"

printf '%s\n' '=== Mars selected user/machine tasks: check mode only; no --diff ==='
ansible-playbook backup-collection.yaml \
  --check --limit mars --tags user,machine \
  --vault-password-file "$HOME/.vault_pass.txt"

printf '%s\n' '=== Working-tree status (no Git commit or push performed) ==='
git status --short
printf '%s\n' 'PASS: 0048 checkout source normalised; source/syntax checks and mars check-mode preview completed'
printf '%s\n' 'REVIEW REQUIRED: Inspect the Ansible task results before authorising any real deployment.'
