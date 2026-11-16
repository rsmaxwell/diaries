#!/usr/bin/env bash
# 0041 Step 8 — read-only security tests plus one controlled idempotent
# reapplication of the previously approved additive Ansible provisioning.
# Non-interactive process only; do not source into an interactive SSH shell.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
on_exit() {
  rc=$?
  if (( rc != 0 )); then
    printf 'FAIL: 0041 Step 8 stopped (exit %s). 03:30 timer cutover NOT requested.\n' "$rc" >&2
  fi
}
trap on_exit EXIT

ssh_host() { ssh -n -T -o BatchMode=yes -o ConnectTimeout=20 "$@"; }

printf '0041 STEP 8 LIVE SECURITY / IDEMPOTENCE: %s on %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$(hostname -s)"
[[ $(hostname -s) == mango ]] || fail 'Run this script on mango'

cd /home/richard/ansible-controller
for item in playbooks inventory; do
  [[ -d $item/.git || -f $item/.git ]] || fail "Missing $item submodule"
done
printf '\n=== Source/inventory revisions and working-tree changes ===\n'
git submodule status
git -C playbooks status --short
[[ -z $(git -C playbooks diff --cached --name-only) ]] || fail 'Playbooks staged modifications require review'
git -C playbooks diff --check

printf '\n=== Capture current production scheduler/service definitions ===\n'
service_before=$(ssh_host mars 'systemctl cat btrfs-native-push.service')
timer_before=$(ssh_host mars 'systemctl cat btrfs-native-push.timer')
enabled_before=$(ssh_host mars 'systemctl is-enabled btrfs-native-push.timer')
active_before=$(ssh_host mars 'systemctl is-active btrfs-native-push.timer')
[[ $service_before == *'User=root'* && $service_before == *'ExecStart=/usr/local/bin/btrfs-simplified-replication sender cycle'* ]] || fail 'Unrecognised live legacy service'
[[ $timer_before == *'OnCalendar=*-*-* 03:30:00 UTC'* && $enabled_before == enabled && $active_before == active ]] || fail 'Existing 03:30 timer is not enabled/active'
ssh_host mars 'test -f /etc/systemd/system/btrfs-native-push-0041-candidate.service'

printf '\n=== Confirm dedicated accounts have no administrative groups ===\n'
ssh_host mars 'test "$(id -Gn btrfs-send)" = btrfs-send && test "$(getent passwd btrfs-send | cut -d: -f7)" = /usr/sbin/nologin && echo "PASS: sender account group and shell"'
ssh_host backup 'test "$(id -Gn btrfs-receive)" = btrfs-receive && test "$(getent passwd btrfs-receive | cut -d: -f7)" = /bin/sh && echo "PASS: receiver account group and shell"'

printf '\n=== Verify receiver key restrictions and non-writable config ===\n'
receiver_key_stat=$(ssh_host backup 'sudo -n stat -c "%U:%G %a" /var/lib/btrfs-receive/.ssh/authorized_keys')
receiver_home_stat=$(ssh_host backup 'sudo -n stat -c "%U:%G %a" /var/lib/btrfs-receive /var/lib/btrfs-receive/.ssh')
[[ $receiver_key_stat == 'root:root 644' ]] || fail 'Receiver authorized_keys is not root:root 0644'
[[ $receiver_home_stat == $'root:root 755\nroot:root 755' ]] || fail 'Receiver home/SSH directory not root-managed'
key_entries=$(ssh_host backup 'sudo -n wc -l < /var/lib/btrfs-receive/.ssh/authorized_keys' | tr -d '[:space:]')
forced_entries=$(ssh_host backup "sudo -n grep -c '^restrict,command=\"/usr/local/libexec/btrfs-replication-ssh-dispatch-0041\" ssh-ed25519 ' /var/lib/btrfs-receive/.ssh/authorized_keys")
[[ $key_entries == 1 && $forced_entries == 1 ]] || fail 'Unexpected receiver authorized_keys entries or restrictions'
if ssh_host backup 'sudo -n -u btrfs-receive test -w /var/lib/btrfs-receive/.ssh/authorized_keys'; then
  fail 'Receiver account unexpectedly able to modify its authorized_keys'
fi
printf 'PASS: single root-managed restricted receiver key; service cannot modify it\n'

printf '\n=== Verify neither dedicated account has unrestricted sudo ===\n'
negative_sudo() {
  local host=$1 account=$2 requested=$3 output rc
  if output=$(ssh_host "$host" "sudo -n -u $account sudo -n $requested" 2>&1); then
    fail "$host:$account unexpectedly allowed sudo $requested"
  else
    rc=$?
  fi
  [[ $rc -ne 255 ]] || fail "SSH failed while testing sudo on $host"
  printf 'PASS: %s rejects sudo %s (exit=%s)\n' "$account" "$requested" "$rc"
}
negative_sudo mars btrfs-send /usr/bin/id
negative_sudo mars btrfs-send '/usr/local/libexec/btrfs-replication-sender-cycle-0041 status'
negative_sudo backup btrfs-receive /usr/bin/id
negative_sudo backup btrfs-receive '/usr/local/libexec/btrfs-replication-receiver-gate-0041 status'
ssh_host mars 'sudo -n visudo -cf /etc/sudoers.d/btrfs-0041-service'
ssh_host backup 'sudo -n visudo -cf /etc/sudoers.d/btrfs-0041-service'

printf '\n=== Verify dedicated SSH status succeeds with pinned key ===\n'
status=$(ssh_host mars 'sudo -n env BTRFS_REPLICATION_IDENTITY_MODE=dedicated /usr/local/bin/btrfs-simplified-replication sender status')
printf '%s\n' "$status" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["receiver_parent_verified"] is True and d["relation"] in ("equal", "receiver-ahead"); print("PASS: dedicated status verifies receiver parent, relation=" + d["relation"])'

printf '\n=== Adversarial forced-command refusals (no Btrfs modifications) ===\n'
receiver_ssh_rejects() {
  local label=$1 command=$2 output rc escaped
  # Only test static, pre-reviewed strings. Shell-quote the remote command.
  printf -v escaped '%q' "$command"
  if output=$(ssh_host mars "sudo -n -u btrfs-send ssh -T -F /dev/null -o BatchMode=yes -o ConnectTimeout=15 -o StrictHostKeyChecking=yes -o IdentitiesOnly=yes -o UserKnownHostsFile=/etc/btrfs-replication-0041/known_hosts -i /var/lib/btrfs-send/.ssh/id_ed25519 -p 39263 btrfs-receive@10.254.22.1 $escaped" 2>&1); then
    fail "Forced-command dispatcher allowed: $label"
  else
    rc=$?
  fi
  [[ $rc == 64 && $output == *'REFUSED:'* ]] || fail "Unexpected refusal for $label (exit=$rc): $output"
  printf 'PASS: receiver rejects %s (exit=64)\n' "$label"
}
receiver_ssh_rejects 'arbitrary id' 'id'
receiver_ssh_rejects 'shell request' 'sh -c id'
receiver_ssh_rejects 'bootstrap' 'btrfs-replication receiver bootstrap'
receiver_ssh_rejects 'shell operator injection' 'btrfs-replication receiver status ; id'
receiver_ssh_rejects 'path traversal' 'btrfs-replication receiver status --snapshot ../../etc/passwd'

printf '\n=== Reapply additive Ansible role and require changed=0 ===\n'
cd /home/richard/ansible-controller
source ./enter.sh
# enter.sh itself changes directory to playbooks; use an absolute path here.
cd /home/richard/ansible-controller/playbooks
if ansible_output=$(ansible-playbook btrfs-replication.yaml \
    --limit 'mars,backup' --tags btrfs-0041-provision \
    -e btrfs_0041_additive_enabled=true \
    --vault-password-file "$HOME/.vault_pass.txt" </dev/null 2>&1); then
  printf '%s\n' "$ansible_output"
else
  printf '%s\n' "$ansible_output"
  fail 'Additive Ansible repeat failed'
fi
printf '%s\n' "$ansible_output" | grep -Eq '^mars[[:space:]]+:.*changed=0[[:space:]]+unreachable=0[[:space:]]+failed=0' || fail 'mars did not converge with changed=0'
printf '%s\n' "$ansible_output" | grep -Eq '^backup[[:space:]]+:.*changed=0[[:space:]]+unreachable=0[[:space:]]+failed=0' || fail 'backup did not converge with changed=0'
printf 'PASS: additive provisioning idempotent on both hosts\n'

printf '\n=== Reconfirm original production service and timer unchanged ===\n'
[[ $(ssh_host mars 'systemctl cat btrfs-native-push.service') == "$service_before" ]] || fail 'Original service changed'
[[ $(ssh_host mars 'systemctl cat btrfs-native-push.timer') == "$timer_before" ]] || fail 'Original timer changed'
[[ $(ssh_host mars 'systemctl is-enabled btrfs-native-push.timer') == "$enabled_before" ]] || fail 'Original timer enablement changed'
[[ $(ssh_host mars 'systemctl is-active btrfs-native-push.timer') == "$active_before" ]] || fail 'Original timer activity changed'
candidate_state=$(ssh_host mars 'systemctl show btrfs-native-push-0041-candidate.service -p ActiveState --value')
[[ $candidate_state != active && $candidate_state != activating ]] || fail 'Candidate service unexpectedly active'
printf 'PASS: 03:30 production timer/service unchanged; candidate not active (%s)\n' "$candidate_state"

printf '\nPASS: 0041 Step 8 security restrictions and idempotence verified; no Btrfs transfer performed\n'
