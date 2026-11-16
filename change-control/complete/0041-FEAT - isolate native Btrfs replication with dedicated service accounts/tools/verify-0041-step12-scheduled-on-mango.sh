#!/usr/bin/env bash
# 0041 Step 12 — read-only verification after the first scheduled 03:30 UTC run.
# Executed only as non-interactive `ssh mango 'bash -s'` from the Cygwin launcher.
set -Eeuo pipefail
export LC_ALL=C.UTF-8
fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
ssh_host() { ssh -n -o BatchMode=yes -o ConnectTimeout=20 "$@"; }
[[ "$(hostname -s)" == mango ]] || fail 'This verifier must run on mango'
[[ $# == 0 ]] || fail 'Unexpected arguments'

expected_date='2026-11-16'
cutover_parent='20261115-140017Z'
first_scheduled_epoch=$(date -u -d '2026-11-16 03:30:00 UTC' +%s)
verify_after_epoch=$(date -u -d '2026-11-16 03:45:00 UTC' +%s)
now_epoch=$(date -u +%s)
printf '0041 STEP 12 READ-ONLY SCHEDULED VERIFICATION: %s UTC on mango\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo 'No Btrfs transfer, pruning, systemd start/stop, snapshot deletion, Ansible change, or state edits.'
(( now_epoch >= verify_after_epoch )) || fail 'Scheduled 16 November 03:30 UTC run not yet ready for post-run verification; do not accept early PASS'

printf '\n=== Controller source identity (read only) ===\n'
cd /home/richard/ansible-controller || fail 'Controller repository missing'
printf 'controller=%s\n' "$(git rev-parse HEAD)"
git submodule status
printf 'playbooks=%s\n' "$(git -C playbooks rev-parse HEAD)"
printf 'inventory=%s\n' "$(git -C inventory rev-parse HEAD)"
echo '--- outstanding Playbooks changes ---'
git -C playbooks status --short
[[ -f playbooks/roles/btrfs-replication/defaults/main.yaml ]] || fail 'Canonical Ansible defaults missing'
grep -Eq '^btrfs_native_sender_service_identity:[[:space:]]*dedicated([[:space:]]*#.*)?$' \
  playbooks/roles/btrfs-replication/defaults/main.yaml || fail 'Permanent Playbooks service identity is not dedicated'

printf '\n=== Canonical sender service and 03:30 timer ===\n'
unit=$(ssh_host mars 'systemctl cat btrfs-native-push.service') || fail 'Cannot read service unit'
timer=$(ssh_host mars 'systemctl cat btrfs-native-push.timer') || fail 'Cannot read timer unit'
printf '%s\n' "$unit"
printf '%s\n' "$timer"
[[ "$unit" == *'User=btrfs-send'* && "$unit" == *'Group=btrfs-send'* ]] || fail 'Sender service identity differs from cutover'
[[ "$unit" == *'ExecStart=/usr/bin/sudo -n /usr/local/libexec/btrfs-replication-sender-cycle-0041'* ]] || fail 'Privileged entrypoint differs from cutover'
[[ "$timer" == *'OnCalendar=*-*-* 03:30:00 UTC'* ]] || fail '03:30 timer definition changed'
[[ $(ssh_host mars 'systemctl is-enabled btrfs-native-push.timer') == enabled ]] || fail 'Timer disabled'
[[ $(ssh_host mars 'systemctl is-active btrfs-native-push.timer') == active ]] || fail 'Timer inactive'
[[ $(ssh_host mars 'systemctl show -P User btrfs-native-push.service') == btrfs-send ]] || fail 'Loaded systemd user is not btrfs-send'
[[ $(ssh_host mars 'systemctl show -P Group btrfs-native-push.service') == btrfs-send ]] || fail 'Loaded systemd group is not btrfs-send'

printf '\n=== Timer trigger and service completion (not merely configuration) ===\n'
timer_last=$(ssh_host mars 'systemctl show -P LastTriggerUSec btrfs-native-push.timer') || fail 'Cannot read last timer trigger'
service_show=$(ssh_host mars 'systemctl show btrfs-native-push.service -p Result -p ExecMainStatus -p ExecMainCode -p ExecMainStartTimestamp -p ExecMainExitTimestamp -p ActiveState -p SubState -p User -p ExecStart') || fail 'Cannot inspect service result'
printf 'Timer LastTriggerUSec=%s\n' "$timer_last"
printf '%s\n' "$service_show"
last_epoch=$(date -u -d "$timer_last" +%s 2>/dev/null) || fail 'Unable to interpret timer LastTriggerUSec'
(( last_epoch >= first_scheduled_epoch && last_epoch <= now_epoch )) || fail 'No 16 November or later timer-triggered execution recorded'
[[ "$service_show" == *'Result=success'* && "$service_show" == *'ExecMainStatus=0'* ]] || fail 'Last sender service did not report success'
[[ "$service_show" != *$'ActiveState=active'* && "$service_show" != *$'ActiveState=activating'* ]] || fail 'Sender service is still running; evaluate once it finishes'
start_date=$(printf '%s\n' "$service_show" | sed -n 's/^ExecMainStartTimestamp=//p')
end_date=$(printf '%s\n' "$service_show" | sed -n 's/^ExecMainExitTimestamp=//p')
start_epoch=$(date -u -d "$start_date" +%s 2>/dev/null) || fail 'Unable to interpret last service start timestamp'
end_epoch=$(date -u -d "$end_date" +%s 2>/dev/null) || fail 'Unable to interpret last service exit timestamp'
(( start_epoch >= first_scheduled_epoch && start_epoch <= now_epoch )) || fail 'Service start is not after scheduled cutover run'
(( end_epoch >= start_epoch && end_epoch <= now_epoch )) || fail 'Service exit timestamp invalid'
printf 'PASS: 03:30 timer triggered and dedicated sender service completed successfully\n'

printf '\n=== Sender journal for scheduled operation ===\n'
journal=$(ssh_host mars "sudo -n journalctl --unit=btrfs-native-push.service --since '2026-11-16 03:20:00' --no-pager --output=short-iso") || fail 'Cannot read sender journal'
printf '%s\n' "$journal"
[[ -n "$journal" && "$journal" != *'-- No entries --'* ]] || fail 'Missing sender journal evidence for scheduled run'

printf '\n=== Independent protected parent and dedicated receiver reconciliation ===\n'
src_sha=$(ssh_host mars 'sudo -n sha256sum /media/usb/@snapshots/.simple-agreed-parent.json' | awk '{print $1}') || fail 'Cannot hash sender agreed parent'
dst_sha=$(ssh_host backup 'sudo -n sha256sum /@data/mars-received/.replication-state/.simple-agreed-parent.json' | awk '{print $1}') || fail 'Cannot hash receiver agreed parent'
[[ "$src_sha" =~ ^[0-9a-f]{64}$ && "$src_sha" == "$dst_sha" ]] || fail 'Sender/receiver agreed-parent records differ'
printf 'Sender agreed-parent SHA256: %s\nReceiver agreed-parent SHA256: %s\n' "$src_sha" "$dst_sha"
src_perms=$(ssh_host mars 'sudo -n stat -c "%U:%G %a %n" /media/usb/@snapshots/.simple-agreed-parent.json /media/usb/@snapshots/.replication-protection.json') || fail 'Cannot verify sender permissions'
dst_perms=$(ssh_host backup 'sudo -n stat -c "%U:%G %a %n" /@data/mars-received/.replication-state/.simple-agreed-parent.json') || fail 'Cannot verify receiver permissions'
printf '%s\n%s\n' "$src_perms" "$dst_perms"
[[ "$src_perms" == *'root:root 600 /media/usb/@snapshots/.simple-agreed-parent.json'* ]] || fail 'Sender agreed-parent permissions changed'
[[ "$src_perms" == *'root:root 600 /media/usb/@snapshots/.replication-protection.json'* ]] || fail 'Sender protection permissions changed'
[[ "$dst_perms" == *'root:root 600 /@data/mars-received/.replication-state/.simple-agreed-parent.json'* ]] || fail 'Receiver agreed-parent permissions changed'
status=$(ssh_host mars 'sudo -n env BTRFS_REPLICATION_IDENTITY_MODE=dedicated /usr/local/bin/btrfs-simplified-replication sender status') || fail 'Dedicated status failed'
printf '%s\n' "$status"
printf '%s\n' "$status" | python3 -c '
import json, sys
s=json.load(sys.stdin)
assert s.get("receiver_parent_verified") is True, "Receiver parent identity not verified"
assert s.get("relation") == "equal", "Sender/receiver relation is not equal"
assert s.get("state") == s.get("receiver"), "Sender/receiver states differ"
parent=s["state"]["parent"]["timestamp"]
assert parent > "20261115-140017Z", f"Agreed parent did not advance beyond Step 10: {parent}"
print("PASS: accepted parent advanced beyond Step 10 to " + parent)
' || fail 'Dedicated status or agreed-parent advancement not accepted'

printf '\n=== Read-only backup health ===\n'
ssh_host mars 'test -x /usr/local/sbin/diaries-backup-status && sudo -n /usr/local/sbin/diaries-backup-status --limit 2' || fail 'Backup health report could not be completed'

printf '\n=== Candidate service must remain inactive ===\n'
candidate_state=$(ssh_host mars 'systemctl show -P ActiveState btrfs-native-push-0041-candidate.service') || fail 'Cannot inspect candidate service'
[[ "$candidate_state" != active && "$candidate_state" != activating ]] || fail 'Staged candidate service unexpectedly active'
printf 'PASS: staged candidate service inactive (%s)\n' "$candidate_state"

printf '\nPASS: 0041 Step 12 first scheduled dedicated-account replication verified; acceptance evidence captured\n'
