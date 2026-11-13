#!/usr/bin/env bash
# Run non-interactively on mango via SSH from authoritative Windows Diaries tree.
# Validates the 0048 candidate, retires the active source manifest, publishes
# Playbooks, then updates/publishes the ansible-controller submodule pin.
set -euo pipefail
controller=/home/richard/ansible-controller
playbooks="$controller/playbooks"
role="$playbooks/roles/backup-collection"
base_controller='f6ba7fec7752f4bbfa1535958500bde9dea3ea84'
base_playbooks='df68a0e3bc57bae29a76f46a58c30835126d7f20'
base_inventory='ebcce026723db37b9b53b76ba21903a351d48466'

printf '%s\n' '0048 STEP 3 — PUBLISH SIMPLIFIED PLAYBOOKS AND CONTROLLER PIN'
printf 'UTC: %s HOST: %s\n' "$(date -u +%FT%TZ)" "$(hostname)"
cd "$controller"
[[ "$(git branch --show-current)" == main ]] || { echo 'FAIL: controller not on main' >&2; exit 1; }
[[ "$(git rev-parse HEAD)" == "$base_controller" ]] || { echo 'FAIL: controller HEAD changed' >&2; exit 1; }
[[ -z "$(git status --porcelain --ignore-submodules=all)" ]] || { echo 'FAIL: controller has local changes' >&2; exit 1; }
[[ "$(git rev-parse HEAD:playbooks)" == "$base_playbooks" ]] || { echo 'FAIL: parent pin changed' >&2; exit 1; }
[[ "$(git rev-parse HEAD:inventory)" == "$base_inventory" ]] || { echo 'FAIL: inventory pin changed' >&2; exit 1; }
[[ "$(git -C inventory rev-parse HEAD)" == "$base_inventory" ]] || { echo 'FAIL: inventory checkout changed' >&2; exit 1; }
[[ -z "$(git -C inventory status --porcelain)" ]] || { echo 'FAIL: inventory checkout dirty' >&2; exit 1; }
git fetch origin main
[[ "$(git rev-parse FETCH_HEAD)" == "$base_controller" ]] || { echo 'FAIL: published controller main advanced' >&2; exit 1; }

cd "$playbooks"
[[ "$(git rev-parse HEAD)" == "$base_playbooks" ]] || { echo 'FAIL: Playbooks HEAD changed' >&2; exit 1; }
[[ -z "$(git diff --cached --name-only)" ]] || { echo 'FAIL: staged Playbooks changes' >&2; exit 1; }
[[ -z "$(git ls-files --others --exclude-standard)" ]] || { echo 'FAIL: untracked Playbooks files' >&2; exit 1; }
actual="$(git diff --name-only | LC_ALL=C sort)"
expected="$(printf '%s\n' \
  roles/backup-collection/README.md \
  roles/backup-collection/tasks/install_user_scripts.yaml \
  roles/backup-collection/tests/verify-collection-source-modes.py | LC_ALL=C sort)"
[[ "$actual" == "$expected" ]] || { echo 'FAIL: unexpected Playbooks tracked changes' >&2; printf '%s\n' "$actual"; exit 1; }
[[ -f "$role/source-modes.json" ]] || { echo 'FAIL: source-modes.json already missing' >&2; exit 1; }
git diff --check

python3 - "$role" <<'PYFILES'
import pathlib, hashlib, sys
role=pathlib.Path(sys.argv[1])
expected={'README.md': '78374e6b5572319adbfc02abfa087b641f6ca8e172887e0ae40aca2755d75aad', 'tasks/install_user_scripts.yaml': '1c27006c86c6f4f89a549bf2a17494363965b2a39460b9d57fe680a8e4d56b48', 'tests/verify-collection-source-modes.py': 'c17f2e0ad0853d1fce6845a93b4027a1b0a975891fa789386676a33a38ca4786'}
for name, sha in expected.items():
 p=role/name
 if not p.is_file() or p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest()!=sha:
  raise SystemExit('FAIL: candidate mismatch: '+name)
print('PASS: candidate files match reviewed package')
PYFILES

printf '%s\n' '=== Verify new preflight and syntax ==='
python3 "$role/tests/verify-collection-source-modes.py"
export ANSIBLE_CONFIG=/etc/ansible/ansible.cfg
export ANSIBLE_INVENTORY="$controller/inventory/hosts"
ansible-playbook backup-collection.yaml --syntax-check --vault-password-file "$HOME/.vault_pass.txt"

printf '%s\n' '=== Verify upstream before publication ==='
git fetch origin main
[[ "$(git rev-parse FETCH_HEAD)" == "$base_playbooks" ]] || { echo 'FAIL: published Playbooks main advanced' >&2; exit 1; }
if git show-ref --verify --quiet refs/heads/main; then
  [[ "$(git rev-parse refs/heads/main)" == "$base_playbooks" ]] || { echo 'FAIL: local Playbooks main points elsewhere' >&2; exit 1; }
  git switch main
else
  git switch -c main
fi
[[ "$(git rev-parse HEAD)" == "$base_playbooks" ]] || { echo 'FAIL: branch switch unexpectedly changed HEAD' >&2; exit 1; }

printf '%s\n' '=== Remove obsolete active manifest, stage exactly four paths ==='
git rm -- roles/backup-collection/source-modes.json
git add -- roles/backup-collection/README.md \
  roles/backup-collection/tasks/install_user_scripts.yaml \
  roles/backup-collection/tests/verify-collection-source-modes.py
actual="$(git diff --cached --name-only | LC_ALL=C sort)"
expected="$(printf '%s\n' \
  roles/backup-collection/README.md \
  roles/backup-collection/source-modes.json \
  roles/backup-collection/tasks/install_user_scripts.yaml \
  roles/backup-collection/tests/verify-collection-source-modes.py | LC_ALL=C sort)"
[[ "$actual" == "$expected" ]] || { echo 'FAIL: staged paths mismatch' >&2; exit 1; }
git diff --cached --check
git diff --cached --stat

git commit -m '0048-FEAT: use Git-native backup collection permissions'
git push origin main
published_playbooks="$(git rev-parse HEAD)"
printf 'PUBLISHED_PLAYBOOKS=%s\n' "$published_playbooks"

printf '%s\n' '=== Publish parent submodule pin ==='
cd "$controller"
[[ "$(git rev-parse HEAD)" == "$base_controller" ]] || { echo 'FAIL: controller changed before pin update' >&2; exit 1; }
git add -- playbooks
[[ "$(git diff --cached --name-only)" == playbooks ]] || { echo 'FAIL: parent staged files unexpected' >&2; exit 1; }
git diff --cached --check
git diff --cached --submodule=log --stat
git commit -m '0048-FEAT: pin simplified backup collection Playbooks'
git push origin main
printf 'PUBLISHED_CONTROLLER=%s\n' "$(git rev-parse HEAD)"
[[ "$(git rev-parse HEAD:playbooks)" == "$published_playbooks" ]] || exit 1
[[ "$(git rev-parse HEAD:inventory)" == "$base_inventory" ]] || exit 1
[[ -z "$(git status --porcelain --ignore-submodules=none)" ]] || { echo 'FAIL: controller/submodule checkout not clean' >&2; exit 1; }
printf '%s\n' 'PASS: 0048 Playbooks and parent pin published; mars deployment not executed'
