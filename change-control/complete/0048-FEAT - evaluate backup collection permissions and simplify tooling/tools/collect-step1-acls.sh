#!/usr/bin/env bash
# 0048-FEAT Step 1: read-only permission/ACL and repository baseline.
# Execute on mango via: ssh mango 'bash -s' < this-file
# Prints metadata only; never reads filter contents or decrypted inventory.
set -Eeuo pipefail

controller=/home/richard/ansible-controller
printf '0048 STEP 1 READ-ONLY ACL COLLECTION\n'
printf 'UTC: '; date -u '+%Y-%m-%dT%H:%M:%SZ'
printf 'HOST: '; hostname
printf '\n=== Controller/submodule revisions and clean-state guards ===\n'
cd -- "$controller"
test "$(git branch --show-current)" = main || { echo 'FAIL: parent not on main'; exit 1; }
for repo in . playbooks inventory; do
  printf '%s HEAD=' "$repo"
  git -C "$repo" rev-parse HEAD
  if test -n "$(git -C "$repo" status --porcelain)"; then
    echo "FAIL: uncommitted or untracked changes in $repo"
    exit 1
  fi
done
if git submodule status | grep -qE '^[-+U]'; then
  echo 'FAIL: submodule checkout does not match the parent pin'
  exit 1
fi
git submodule status

printf '\n=== Effective Ansible entry point (path only) ===\n'
source "$controller/enter.sh"
test "$ANSIBLE_INVENTORY" = "$controller/inventory/hosts"
printf 'ANSIBLE_CONFIG=%s\nANSIBLE_INVENTORY=%s\n' "$ANSIBLE_CONFIG" "$ANSIBLE_INVENTORY"

command -v getfacl >/dev/null 2>&1 || {
  echo 'INCOMPLETE: getfacl unavailable on mango; no permissions changed'
  exit 2
}

printf '\n=== Mango source metadata: 14 historical contract entries ===\n'
id richard
for path in \
  roles/backup-collection/files/backup \
  roles/backup-collection/files/backup/home \
  roles/backup-collection/files/backup/home/includes \
  roles/backup-collection/files/backup/home/excludes-1 \
  roles/backup-collection/files/backup/home/excludes-2 \
  roles/backup-collection/files/backup-machine \
  roles/backup-collection/files/backup-machine/home \
  roles/backup-collection/files/backup-machine/home/includes \
  roles/backup-collection/files/backup-machine/home/excludes-1 \
  roles/backup-collection/files/backup-machine/home/excludes-2 \
  roles/backup-collection/files/backup-machine/remote \
  roles/backup-collection/files/backup-machine/remote/includes \
  roles/backup-collection/files/backup-machine/remote/excludes-1 \
  roles/backup-collection/files/backup-machine/remote/excludes-2
do
  echo "--- SOURCE: $path ---"
  test ! -L "$path" || { echo 'FAIL: unexpected source symlink'; exit 1; }
  stat -c '%F %a %U:%G %n' -- "$path"
  getfacl -cp -- "$path"
done

printf '\n=== Mars installed metadata and parent-directory access ===\n'
ssh mars 'sudo -n bash -s' <<'MARS'
set -Eeuo pipefail
command -v getfacl >/dev/null 2>&1 || {
  echo 'INCOMPLETE: getfacl unavailable on mars; no permissions changed'
  exit 2
}
printf 'HOST: '; hostname
id richard
for path in \
  /home/richard \
  /home/richard/scripts \
  /home/richard/scripts/backup \
  /home/richard/scripts/backup/home \
  /home/richard/scripts/backup/home/includes \
  /home/richard/scripts/backup/home/excludes-1 \
  /home/richard/scripts/backup/home/excludes-2 \
  /root \
  /root/scripts \
  /root/scripts/backup \
  /root/scripts/backup/home \
  /root/scripts/backup/home/includes \
  /root/scripts/backup/home/excludes-1 \
  /root/scripts/backup/home/excludes-2 \
  /root/scripts/backup/remote \
  /root/scripts/backup/remote/includes \
  /root/scripts/backup/remote/excludes-1 \
  /root/scripts/backup/remote/excludes-2
do
  echo "--- INSTALLED: $path ---"
  test ! -L "$path" || { echo 'FAIL: unexpected installed symlink'; exit 1; }
  stat -c '%F %a %U:%G %n' -- "$path"
  getfacl -cp -- "$path"
done
MARS
printf '\nPASS: 0048 Step 1 read-only ACL collection (no changes made)\n'
