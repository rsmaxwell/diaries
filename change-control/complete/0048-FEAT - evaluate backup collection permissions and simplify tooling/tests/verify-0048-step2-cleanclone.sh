#!/usr/bin/env bash
# 0048 Step 2 disposable clean-clone and local Ansible mode-convergence test.
# Stream from Windows: ssh mango 'bash -s' < this-script
# All writes occur beneath a mktemp directory on mango; no host deployment.
set -Eeuo pipefail
umask 022

controller='/home/richard/ansible-controller'
tmpdir=''
cleanup() {
  if [[ -n "$tmpdir" && -d "$tmpdir" ]]; then
    rm -rf -- "$tmpdir"
  fi
}
trap cleanup EXIT

printf '0048 STEP 2 DISPOSABLE CLEAN-CHECKOUT TEST\nUTC: '
date -u '+%Y-%m-%dT%H:%M:%SZ'
printf 'HOST: '; hostname
printf 'USER: '; id -un
[[ "$(id -u)" -ne 0 ]] || { echo 'FAIL: refuse execution as root'; exit 1; }
for app in git python3 ansible-playbook rsync stat mktemp; do
  command -v "$app" >/dev/null 2>&1 || { printf 'FAIL: missing %s\n' "$app"; exit 1; }
done

cd -- "$controller"
[[ "$(git branch --show-current)" = 'main' ]] || { echo 'FAIL: parent not main'; exit 1; }
for repo in . playbooks inventory; do
  [[ -z "$(git -C "$repo" status --porcelain)" ]] || { echo "FAIL: working tree not clean: $repo"; exit 1; }
done
if git submodule status | grep -qE '^[-+U]'; then
  echo 'FAIL: controller submodule mismatch'; exit 1
fi
expected="$(git -C playbooks rev-parse HEAD)"
[[ "$(git rev-parse :playbooks)" = "$expected" ]] || { echo 'FAIL: Playbooks differs from controller pin'; exit 1; }
remote="$(git -C playbooks remote get-url origin)"
printf 'CONTROLLER=%s\nPLAYBOOKS=%s\nINVENTORY=%s\nPLAYBOOKS_REMOTE=%s\n' \
  "$(git rev-parse HEAD)" "$expected" "$(git -C inventory rev-parse HEAD)" "$remote"

tmpdir="$(mktemp -d "${TMPDIR:-/tmp}/0048-step2.XXXXXXXX")"
clone="$tmpdir/clean-playbooks"
target="$tmpdir/disposable-target"
mkdir -p -- "$target"

printf '\n=== Clone published Playbooks and detach at frozen revision ===\n'
git clone --quiet --no-checkout "$remote" "$clone"
git -C "$clone" checkout --quiet --detach "$expected"
[[ "$(git -C "$clone" rev-parse HEAD)" = "$expected" ]] || { echo 'FAIL: unexpected clone revision'; exit 1; }
[[ -z "$(git -C "$clone" status --porcelain)" ]] || { echo 'FAIL: new checkout not clean'; exit 1; }
printf 'CLEAN_CLONE=%s\n' "$(git -C "$clone" rev-parse HEAD)"

printf '\n=== 14-source-mode inventory and frozen hash comparison ===\n'
python3 - "$clone" <<'PYMODES'
import hashlib, json, os, pathlib, stat, sys
root = pathlib.Path(sys.argv[1]) / 'roles' / 'backup-collection'
contract = json.loads((root/'source-modes.json').read_text())
entries = contract['entries']
if len(entries) != 14:
    raise SystemExit('FAIL: expected 14 contract entries')
for item in entries:
    p = root / item['path']
    if p.is_symlink() or not p.exists():
        raise SystemExit(f'FAIL: source missing/symlink {p}')
    s = p.stat()
    actual = stat.S_IMODE(s.st_mode)
    kind = 'directory' if p.is_dir() else 'file'
    if kind != item['kind']:
        raise SystemExit(f'FAIL: type mismatch {p}')
    if p.is_file():
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        if digest != item['sha256']:
            raise SystemExit(f'FAIL: hash mismatch {p}')
    print(f'{kind:9s}  clone={actual:04o} historical={item["mode"]} {item["path"]}')
print('PASS: 14 clean-clone paths/types and nine content hashes verified')
PYMODES

printf '\n=== Build disposable Ansible harness (local-only targets) ===\n'
cat > "$tmpdir/local-mode-harness.yaml" <<'YAML'
---
- name: 0048 Step 2 local-only source-mode convergence test
  hosts: localhost
  connection: local
  gather_facts: false
  become: false
  tasks:
    - name: User install | Create directories as production role does
      ansible.builtin.file:
        path: "{{ target_root }}/user/{{ item }}"
        state: directory
        mode: '0750'
      loop:
        - ''
        - cron
        - home

    - name: User install | Archive-mode sync with production options
      ansible.posix.synchronize:
        archive: true
        src: "{{ clone_root }}/roles/backup-collection/files/backup/"
        dest: "{{ target_root }}/user/"
        rsync_opts:
          - '--omit-dir-times'
          - '--exclude=__pycache__/'
          - '--exclude=*.pyc'

    - name: Machine install | Create directories as production role does
      ansible.builtin.file:
        path: "{{ target_root }}/machine/{{ item }}"
        state: directory
      loop:
        - ''
        - cron
        - home
        - remote

    - name: Machine install | Archive-mode sync with production options
      ansible.posix.synchronize:
        archive: true
        src: "{{ clone_root }}/roles/backup-collection/files/backup-machine/"
        dest: "{{ target_root }}/machine/"
        rsync_opts:
          - '--omit-dir-times'
          - '--exclude=diaries-pull.py'
          - '--exclude=__pycache__/'
          - '--exclude=*.pyc'
YAML

python3 - "$clone" "$target" "$tmpdir/vars.json" <<'PYVARS'
import json, sys
with open(sys.argv[3], 'w') as f:
    json.dump({'clone_root':sys.argv[1], 'target_root':sys.argv[2]}, f)
PYVARS

printf '\n=== Ansible run 1 / new disposable target ===\n'
ANSIBLE_INVENTORY='localhost,' ansible-playbook -i localhost, -c local \
  "$tmpdir/local-mode-harness.yaml" -e "@$tmpdir/vars.json" | tee "$tmpdir/run1.log"

printf '\n=== Final destination modes after run 1 ===\n'
for path in "$target/user" "$target/user/home" "$target/machine" "$target/machine/home" "$target/machine/remote"; do
  stat -c '%a %U:%G %n' "$path"
done

printf '\n=== Ansible run 2 / same disposable target ===\n'
ANSIBLE_INVENTORY='localhost,' ansible-playbook -i localhost, -c local \
  "$tmpdir/local-mode-harness.yaml" -e "@$tmpdir/vars.json" | tee "$tmpdir/run2.log"

printf '\n=== Final destination modes after run 2 ===\n'
for path in "$target/user" "$target/user/home" "$target/machine" "$target/machine/home" "$target/machine/remote"; do
  stat -c '%a %U:%G %n' "$path"
done

changed="$(sed -nE '/^localhost[[:space:]]*:/s/.*changed=([0-9]+).*/\1/p' "$tmpdir/run2.log" | tail -n 1)"
[[ "$changed" =~ ^[0-9]+$ ]] || { echo 'FAIL: cannot parse run 2 recap'; exit 1; }
printf '\nRUN2_CHANGED=%s\n' "$changed"
if [[ "$changed" -eq 0 ]]; then
  echo 'PASS: Disposable Ansible mode tasks converged (run 2 changed=0)'
else
  echo 'OBSERVED: Disposable Ansible mode tasks did NOT converge on run 2.'
  echo 'STEP2 B3: FAIL / corrective Playbooks design required. This is a valid diagnostic result, not a production failure.'
fi
printf 'PASS: Clean-clone experiment completed; temporary target will be removed\n'
