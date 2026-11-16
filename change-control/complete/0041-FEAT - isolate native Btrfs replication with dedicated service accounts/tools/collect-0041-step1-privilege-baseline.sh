#!/usr/bin/env bash
# 0041-FEAT Step 1: read-only, evidence-safe current privilege baseline.
# Run with: ssh mango 'bash -s' < this-file
# Does not print private keys, authorized_keys contents, Vault files, or protected-state contents.
set -Eeuo pipefail

stamp() { date -u +'%Y-%m-%dT%H:%M:%SZ'; }
section() { printf '\n=== %s ===\n' "$1"; }

printf '0041-FEAT STEP 1 — READ-ONLY PRIVILEGE / REPLICATION BASELINE\n'
printf 'TIME_UTC=%s  EXECUTION_HOST=%s  USER=%s\n' "$(stamp)" "$(hostname -s)" "$(id -un)"
if [[ $(hostname -s) != mango ]]; then
    printf 'FAIL: Run from the Ansible controller mango (no commands executed elsewhere)\n' >&2
    exit 1
fi
cd /home/richard/ansible-controller || exit 1
section 'Git identity and source revisions (no checkout mutations)'
for repo in . playbooks inventory; do
    printf 'REPO=%s HEAD=%s BRANCH=%s\n' "$repo" \
        "$(git -C "$repo" rev-parse HEAD)" \
        "$(git -C "$repo" branch --show-current || true)"
    if [[ -z $(git -C "$repo" status --porcelain) ]]; then
        printf 'REPO_CLEAN=%s yes\n' "$repo"
    else
        printf 'REPO_CLEAN=%s no (preserve existing changes; no write performed)\n' "$repo"
    fi
done
git submodule status
section 'Static source and installed Btrfs runtime hashes'
source_file='playbooks/roles/btrfs-replication/files/btrfs-simplified-replication.py'
sha256sum "$source_file"
section 'Effective Ansible path names (without inventory secrets)'
printf 'ANSIBLE_CONFIG=%s\n' "${ANSIBLE_CONFIG:-<unset>}"
printf 'ANSIBLE_INVENTORY=%s\n' "${ANSIBLE_INVENTORY:-<unset>}"

section 'mars — source/sender (read-only)'
ssh -T -o BatchMode=yes -o ConnectTimeout=15 mars 'sudo -n bash -s' <<'MARS'
set -Eeuo pipefail
printf 'HOST=%s UTC=%s\n' "$(hostname -s)" "$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
for name in richard btrfs-send btrfs-receive; do
    if getent passwd "$name" >/dev/null; then
        getent passwd "$name" | awk -F: '{print "ACCOUNT " $1 " uid=" $3 " gid=" $4 " home=" $6 " shell=" $7}'
    else
        printf 'ACCOUNT %s ABSENT\n' "$name"
    fi
done
printf 'RICHARD_ADMIN_SUDO: '
if runuser -u richard -- sudo -n /usr/bin/id -u </dev/null | grep -qx '0'; then echo PASS; else echo 'FAIL: richard passwordless sudo'; exit 1; fi
printf '\n--- systemd sender service and timer ---\n'
systemctl show btrfs-native-push.service -p LoadState -p User -p Group -p ExecStart -p ActiveState -p SubState --no-pager
systemctl show btrfs-native-push.timer -p Unit -p ActiveState -p UnitFileState -p NextElapseUSecRealtime --no-pager
systemctl cat btrfs-native-push.service btrfs-native-push.timer --no-pager
printf '\n--- source root-protected path metadata (not contents) ---\n'
for p in \
  /media/usb /media/usb/@snapshots /media/usb/@snapshots/@data \
  /media/usb/@snapshots/.simple-agreed-parent.json \
  /media/usb/@snapshots/.replication-protection.json \
  /run/lock/btrfs-snapshot-manager.lock \
  /usr/local/bin/btrfs-simplified-replication \
  /home/richard/.ssh /home/richard/.ssh/authorized_keys; do
    if test -e "$p"; then stat -c '%F %a %U:%G %n' -- "$p"; else printf 'ABSENT %s\n' "$p"; fi
done
sha256sum /usr/local/bin/btrfs-simplified-replication
printf '\n--- read-only backup health (does not initiate backup) ---\n'
if test -x /usr/local/sbin/diaries-backup-status; then
    if ! /usr/local/sbin/diaries-backup-status --limit 2 </dev/null; then
        echo 'WARNING: status unavailable; preserve diagnostic rather than claiming healthy'
    fi
else
    echo 'WARNING: diaries-backup-status is absent'
fi
printf '\n--- sender protocol status (read-only, no transfer) ---\n'
if ! /usr/local/bin/btrfs-simplified-replication sender status </dev/null; then
    echo 'WARNING: sender status unavailable, e.g. contention or remote SSH; investigate before cutover'
fi
MARS

section 'backup — receiver/prune (read-only)'
ssh -T -o BatchMode=yes -o ConnectTimeout=15 backup 'sudo -n bash -s' <<'BACKUP'
set -Eeuo pipefail
printf 'HOST=%s UTC=%s\n' "$(hostname -s)" "$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
for name in richard btrfs-send btrfs-receive; do
    if getent passwd "$name" >/dev/null; then
        getent passwd "$name" | awk -F: '{print "ACCOUNT " $1 " uid=" $3 " gid=" $4 " home=" $6 " shell=" $7}'
    else
        printf 'ACCOUNT %s ABSENT\n' "$name"
    fi
done
printf 'RICHARD_ADMIN_SUDO: '
if runuser -u richard -- sudo -n /usr/bin/id -u </dev/null | grep -qx '0'; then echo PASS; else echo 'FAIL: richard passwordless sudo'; exit 1; fi
printf '\n--- receiver retention systemd ---\n'
systemctl show btrfs-receiver-simple-prune.service -p LoadState -p User -p Group -p ExecStart -p ActiveState -p SubState --no-pager
systemctl show btrfs-receiver-simple-prune.timer -p Unit -p ActiveState -p UnitFileState -p NextElapseUSecRealtime --no-pager
systemctl cat btrfs-receiver-simple-prune.service btrfs-receiver-simple-prune.timer --no-pager
printf '\n--- receiver protected paths and SSH credential metadata (not contents) ---\n'
for p in \
  /@data/mars-received /@data/mars-received/@data \
  /@data/mars-received/.replication-state \
  /@data/mars-received/.replication-state/.simple-agreed-parent.json \
  /@data/mars-received/.replication-state/writer.lock \
  /run/lock/btrfs-snapshot-manager.lock \
  /etc/btrfs-receiver-checkpoint-holds.json \
  /etc/btrfs-snapshot-manager.json \
  /usr/local/bin/btrfs-simplified-replication \
  /home/richard/.ssh /home/richard/.ssh/authorized_keys; do
    if test -e "$p"; then stat -c '%F %a %U:%G %n' -- "$p"; else printf 'ABSENT %s\n' "$p"; fi
done
sha256sum /usr/local/bin/btrfs-simplified-replication
printf '\n--- receiver protocol status (read-only, no transfer) ---\n'
if ! /usr/local/bin/btrfs-simplified-replication receiver status </dev/null; then
    echo 'WARNING: receiver status unavailable, e.g. lock contention; investigate before cutover'
fi
printf '\n--- global sshd policy (Match-user rules require later targeted review) ---\n'
if command -v sshd >/dev/null 2>&1; then
    sshd -T | grep -E '^(passwordauthentication|pubkeyauthentication|permittty|allowtcpforwarding|allowagentforwarding|x11forwarding|authorizedkeysfile|forcecommand|permitrootlogin) ' || true
elif test -x /usr/sbin/sshd; then
    /usr/sbin/sshd -T | grep -E '^(passwordauthentication|pubkeyauthentication|permittty|allowtcpforwarding|allowagentforwarding|x11forwarding|authorizedkeysfile|forcecommand|permitrootlogin) ' || true
else
    echo 'WARNING: sshd command unavailable'
fi
BACKUP

section 'Result'
printf 'PASS: read-only baseline collected on mango, mars and backup; no user, key, sudo, filesystem, timer or snapshot changes made\n'
