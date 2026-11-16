#!/usr/bin/env bash
# Step 10: supervised, single-shot dedicated-identity production transfer.
# No transport cutover, scheduler alteration, state rollback, fixture deletion or retries.
# Execute on mango ONLY through the feature's Cygwin launcher.
set -Eeuo pipefail
export LC_ALL=C

fail() { echo "FAIL: $*" >&2; exit 1; }
mode="${1:-}"
[[ $# -eq 1 && ( "$mode" == --preflight || "$mode" == --execute ) ]] || fail 'Usage: bash -s -- --preflight|--execute'
[[ $(hostname -s) == mango ]] || fail 'This script must execute on mango'
cd /home/richard/ansible-controller/playbooks || fail 'Playbooks checkout missing'

started=0
on_exit() {
  rc=$?
  if (( rc != 0 )); then
    echo "FAIL: Step 10 stopped (exit $rc). Do not retry or restore agreed-parent JSON automatically." >&2
    if (( started )); then
      echo '=== Failure diagnostics: read-only current parent and service status ===' >&2
      ssh -n -o BatchMode=yes mars 'sudo -n env BTRFS_REPLICATION_IDENTITY_MODE=dedicated /usr/local/bin/btrfs-simplified-replication sender status' >&2 || true
      ssh -n -o BatchMode=yes backup 'sudo -n /usr/local/bin/btrfs-simplified-replication receiver status' >&2 || true
      ssh -n -o BatchMode=yes mars 'systemctl is-active btrfs-native-push.service || true' >&2 || true
      echo 'Receiver-ahead is possible after lost acknowledgement: inspect both sides before deciding on reconciliation.' >&2
    fi
  fi
}
trap on_exit EXIT

echo "0041 STEP 10 ${mode}: $(date -u +%Y-%m-%dT%H:%M:%SZ) on mango"
echo 'No production timer cutover, no automatic retry, and no state-file rollback.'

echo '=== Source/installed runtime identity ==='
[[ $(git rev-parse HEAD) == c5109340a2fe13296a2343c682e1079d1a212c8d ]] || fail 'Playbooks revision changed; review before execution'
[[ $(git -C ../inventory rev-parse HEAD) == ebcce026723db37b9b53b76ba21903a351d48466 ]] || fail 'Inventory revision changed; review before execution'
# Require the exact candidate validated at Steps 7-9.
check_source() {
  local expected="$1" path="$2" installed="$3" host="$4" actual
  [[ $(sha256sum "$path" | awk '{print $1}') == "$expected" ]] || fail "Candidate source differs: $path"
  actual=$(ssh -n -o BatchMode=yes "$host" "sha256sum '$installed'" | awk '{print $1}')
  [[ "$actual" == "$expected" ]] || fail "Installed runtime differs: $host:$installed"
  echo "PASS: $host:$installed"
}
check_source 01bc877c52ef1051f2f00d4058d740c53af34e1c4cb2545a3e066a6530787a20 roles/btrfs-replication/files/btrfs-simplified-replication.py /usr/local/bin/btrfs-simplified-replication mars
check_source 01bc877c52ef1051f2f00d4058d740c53af34e1c4cb2545a3e066a6530787a20 roles/btrfs-replication/files/btrfs-simplified-replication.py /usr/local/bin/btrfs-simplified-replication backup
check_source 334cc199ef36465dae2d8c817b676fc47e534807f7a0358a231190dd4d22e76a roles/btrfs-replication/files/btrfs-replication-sender-cycle-0041.sh /usr/local/libexec/btrfs-replication-sender-cycle-0041 mars
check_source 689f7ba5bc067859f745704c7b2e298814a7fe71918d058747542931ef6c68bc roles/btrfs-replication/files/btrfs-replication-receiver-gate-0041.py /usr/local/libexec/btrfs-replication-receiver-gate-0041 backup
check_source 8f1f602a8f695e01df984ce58d2de9d6d841799d0b9ab843f1ed91b59c35706f roles/btrfs-replication/files/btrfs-replication-ssh-dispatch-0041.py /usr/local/libexec/btrfs-replication-ssh-dispatch-0041 backup

echo '=== Capture original active service and timer definitions ==='
service_before=$(ssh -n -o BatchMode=yes mars 'systemctl cat btrfs-native-push.service')
timer_before=$(ssh -n -o BatchMode=yes mars 'systemctl cat btrfs-native-push.timer')
[[ "$service_before" == *'User=root'* && "$service_before" == *'ExecStart=/usr/local/bin/btrfs-simplified-replication sender cycle'* ]] || fail 'Legacy service differs from reviewed configuration'
[[ "$timer_before" == *'OnCalendar=*-*-* 03:30:00 UTC'* ]] || fail 'Legacy timer schedule differs'
[[ $(ssh -n -o BatchMode=yes mars 'systemctl is-enabled btrfs-native-push.timer') == enabled ]] || fail 'Legacy timer not enabled'
[[ $(ssh -n -o BatchMode=yes mars 'systemctl is-active btrfs-native-push.timer') == active ]] || fail 'Legacy timer not active'
[[ $(ssh -n -o BatchMode=yes mars 'systemctl is-active btrfs-native-push.service || true') != active ]] || fail 'Scheduled sender already running'
[[ $(ssh -n -o BatchMode=yes backup 'systemctl is-active btrfs-receiver-simple-prune.service || true') != active ]] || fail 'Receiver prune already running'
[[ $(ssh -n -o BatchMode=yes mars 'systemctl is-active btrfs-snapshot-create.service || true') != active ]] || fail 'Source snapshot creation currently running'
[[ $(ssh -n -o BatchMode=yes mars 'systemctl is-active btrfs-snapshot-prune.service || true') != active ]] || fail 'Source snapshot prune currently running'
[[ $(ssh -n -o BatchMode=yes mars 'systemctl is-active btrfs-native-push-0041-candidate.service || true') != active ]] || fail 'Candidate unit already active'
[[ $(ssh -n -o BatchMode=yes mars 'test -f /etc/systemd/system/btrfs-native-push-0041-candidate.service && echo staged') == staged ]] || fail 'Candidate unit not staged'

source_state_path='/media/usb/@snapshots/.simple-agreed-parent.json'
receiver_state_path='/@data/mars-received/.replication-state/.simple-agreed-parent.json'
source_state_metadata_before=$(ssh -n -o BatchMode=yes mars 'sudo -n stat -c "%U:%G %a %n" /media/usb/@snapshots/.simple-agreed-parent.json /media/usb/@snapshots/.replication-protection.json /run/lock/btrfs-snapshot-manager.lock')
receiver_state_metadata_before=$(ssh -n -o BatchMode=yes backup 'sudo -n stat -c "%U:%G %a %n" /@data/mars-received/.replication-state /@data/mars-received/.replication-state/.simple-agreed-parent.json /@data/mars-received/.replication-state/writer.lock')
[[ "$source_state_metadata_before" == *'root:root 600 /media/usb/@snapshots/.simple-agreed-parent.json'* ]] || fail 'Source agreed-parent mode/owner drifted'
[[ "$receiver_state_metadata_before" == *'root:root 600 /@data/mars-received/.replication-state/.simple-agreed-parent.json'* ]] || fail 'Receiver agreed-parent mode/owner drifted'

before_source_sha=$(ssh -n -o BatchMode=yes mars "sudo -n sha256sum '$source_state_path'" | awk '{print $1}')
before_receiver_sha=$(ssh -n -o BatchMode=yes backup "sudo -n sha256sum '$receiver_state_path'" | awk '{print $1}')
[[ "$before_source_sha" =~ ^[0-9a-f]{64}$ && "$before_receiver_sha" =~ ^[0-9a-f]{64}$ ]] || fail 'Cannot read baseline agreed-parent checksums'
echo "Before source state sha256: $before_source_sha"
echo "Before receiver state sha256: $before_receiver_sha"

echo '=== Dedicated transport read-only preflight ==='
before_json=$(ssh -n -o BatchMode=yes mars 'sudo -n env BTRFS_REPLICATION_IDENTITY_MODE=dedicated /usr/local/bin/btrfs-simplified-replication sender status') || fail 'Dedicated preflight failed'
echo "$before_json"
parsed=$(python3 -c '
import json,re,sys
x=json.loads(sys.argv[1]); p=x["preflight"]
assert x["receiver_parent_verified"] is True and x["relation"]=="equal" and x["state"]==x["receiver"], "Agreed-parent identity mismatch"
assert p["action"]=="incremental", "No ordinary incremental transfer available: "+p["action"]
assert re.fullmatch(r"[0-9]{8}-[0-9]{6}Z",p["source"]), "Unsafe candidate"
assert re.fullmatch(r"[0-9a-f-]{36}",p["source_uuid"]), "Unsafe candidate UUID"
assert p["parent"]==x["state"]["parent"]["timestamp"], "Parent changed"
print(p["source"],p["parent"],p["source_uuid"],sep="|")
' "$before_json") || fail 'Preflight declined transfer; no modifications made'
IFS='|' read -r selected_snapshot original_parent selected_uuid <<< "$parsed"
[[ "$selected_snapshot" =~ ^[0-9]{8}-[0-9]{6}Z$ ]] || fail 'Invalid selected snapshot'
echo "Selected candidate: $selected_snapshot"
echo "Agreed parent: $original_parent"

echo '=== Refuse if target candidate already exists (prevents incomplete-candidate deletion) ==='
receiver_candidate_json=$(ssh -n -o BatchMode=yes backup "sudo -n /usr/local/bin/btrfs-simplified-replication receiver status --snapshot $selected_snapshot") || fail 'Receiver candidate inspection failed'
python3 -c '
import json,sys
b=json.loads(sys.argv[1]); d=json.loads(sys.argv[2]);
assert b["candidate"] is None, "Candidate already exists: refuse any potential cleanup"
assert b["state"]==d["state"], "Receiver state changed since preflight"
print("PASS: selected receiver candidate absent; no cleanup required")
' "$receiver_candidate_json" "$before_json" || fail 'Candidate already exists or state changed'

echo '=== Verify sender manager-lock contention is refused ==='
ssh -n -o BatchMode=yes mars \
  "sudo -n flock -n /run/lock/btrfs-snapshot-manager.lock sh -c 'sudo -n env BTRFS_REPLICATION_IDENTITY_MODE=dedicated /usr/local/bin/btrfs-simplified-replication sender status >/dev/null 2>&1; test \$? -eq 75'" \
  || fail 'Sender lock contention was not correctly refused'
echo 'PASS: concurrent sender status refused while manager lock held'

# Re-run final read-only preflight to minimise check/act drift.
last_json=$(ssh -n -o BatchMode=yes mars 'sudo -n env BTRFS_REPLICATION_IDENTITY_MODE=dedicated /usr/local/bin/btrfs-simplified-replication sender status') || fail 'Last preflight failed'
python3 -c 'import json,sys; a=json.loads(sys.argv[1]); b=json.loads(sys.argv[2]); assert a["state"]==b["state"] and a["receiver"]==b["receiver"] and a["preflight"]==b["preflight"], "Preflight changed; repeat later"; print("PASS: final preflight stable")' "$before_json" "$last_json" || fail 'Final preflight changed'

if [[ "$mode" == --preflight ]]; then
  [[ $(ssh -n -o BatchMode=yes mars "sudo -n sha256sum '$source_state_path'" | awk '{print $1}') == "$before_source_sha" ]] || fail 'Read-only preflight changed source state'
  [[ $(ssh -n -o BatchMode=yes backup "sudo -n sha256sum '$receiver_state_path'" | awk '{print $1}') == "$before_receiver_sha" ]] || fail 'Read-only preflight changed receiver state'
  echo 'PASS: 0041 Step 10 preflight-only complete; no transfer or state changes'
  exit 0
fi

# The 03:30 sender / 04:15 receiver prune are left enabled. Refuse a manual
# cycle if its permitted six-hour runtime could overlap the next timer, or if
# we are currently inside the maintenance window.
window_ok=$(python3 -c '
from datetime import datetime,timedelta,timezone
now=datetime.now(timezone.utc)
if 2 <= now.hour < 6: print("no")
else:
    next_run=now.replace(hour=3,minute=30,second=0,microsecond=0)
    if next_run <= now: next_run += timedelta(days=1)
    print("yes" if (next_run-now).total_seconds() > 7*3600 else "no")
') || fail 'Could not check schedule window'
[[ "$window_ok" == yes ]] || fail 'Manual transfer too close to 03:30/04:15 maintenance; choose another daytime window'

echo '=== Authorised ONE supervised production incremental transfer via dedicated identities ==='
echo 'Starting btrfs-send account fixed sudo gate. No automatic retry.'
started=1
# The remote program maintains the existing source manager lock for the whole
# operation; the SSH connection is intentionally delegated to btrfs-send.
# The outer -n prevents consuming the controller script from stdin.
ssh -n -o BatchMode=yes mars 'sudo -n -u btrfs-send sudo -n /usr/local/libexec/btrfs-replication-sender-cycle-0041' \
  || fail 'Dedicated sender cycle returned failure; do not rerun blindly'

echo '=== Read-only independent post-transfer verification ==='
after_json=$(ssh -n -o BatchMode=yes mars 'sudo -n env BTRFS_REPLICATION_IDENTITY_MODE=dedicated /usr/local/bin/btrfs-simplified-replication sender status') || fail 'Post-transfer dedicated status failed'
echo "$after_json"
new_parent=$(python3 -c '
import json,sys
b=json.loads(sys.argv[1]); a=json.loads(sys.argv[2]);
assert a["receiver_parent_verified"] is True and a["relation"]=="equal", "Receiver parent invalid or ahead"
assert a["state"]==a["receiver"], "Source/receiver agreed-parent diverged"
old=b["state"]["parent"]; new=a["state"]["parent"]
assert new["timestamp"] > old["timestamp"], "No parent advancement"
assert a["state"]["prior"]==old, "Prior record does not match old parent"
print(new["timestamp"])
' "$before_json" "$after_json") || fail 'Post-transfer state or parent verification failed'
[[ "$new_parent" =~ ^[0-9]{8}-[0-9]{6}Z$ ]] || fail 'Invalid advanced parent'
receiver_readback=$(ssh -n -o BatchMode=yes backup "sudo -n /usr/local/bin/btrfs-simplified-replication receiver status --snapshot $new_parent") || fail 'Independent receiver readback failed'
python3 -c '
import json,sys
s=json.loads(sys.argv[1]); r=json.loads(sys.argv[2]);
assert r["state"]==s["state"], "Independent receiver record mismatch"
assert r["candidate"] is not None and r["candidate"].get("Received UUID")==s["state"]["parent"]["uuid"], "Btrfs Received UUID mismatch"
assert r["candidate"].get("Flags")=="readonly", "Received snapshot not readonly"
print("PASS: receiver readback / UUID / readonly snapshot verified")
' "$after_json" "$receiver_readback" || fail 'Post-transfer independent receiver UUID check failed'

[[ $(ssh -n -o BatchMode=yes mars 'systemctl cat btrfs-native-push.service') == "$service_before" ]] || fail 'Production sender service definition changed'
[[ $(ssh -n -o BatchMode=yes mars 'systemctl cat btrfs-native-push.timer') == "$timer_before" ]] || fail 'Production sender timer changed'
[[ $(ssh -n -o BatchMode=yes mars 'systemctl is-enabled btrfs-native-push.timer') == enabled ]] || fail 'Production sender timer disabled'
[[ $(ssh -n -o BatchMode=yes mars 'systemctl is-active btrfs-native-push.timer') == active ]] || fail 'Production sender timer inactive'
[[ $(ssh -n -o BatchMode=yes mars 'sudo -n stat -c "%U:%G %a %n" /media/usb/@snapshots/.simple-agreed-parent.json /media/usb/@snapshots/.replication-protection.json /run/lock/btrfs-snapshot-manager.lock') == "$source_state_metadata_before" ]] || fail 'Source state permissions changed'
[[ $(ssh -n -o BatchMode=yes backup 'sudo -n stat -c "%U:%G %a %n" /@data/mars-received/.replication-state /@data/mars-received/.replication-state/.simple-agreed-parent.json /@data/mars-received/.replication-state/writer.lock') == "$receiver_state_metadata_before" ]] || fail 'Receiver state permissions changed'
[[ $(ssh -n -o BatchMode=yes mars 'systemctl is-active btrfs-native-push-0041-candidate.service || true') != active ]] || fail 'Candidate sender service unexpectedly active'

echo "PASS: common parent advanced from $original_parent to $new_parent using dedicated SSH identities"
echo 'PASS: production 03:30 service/timer unchanged, no retries and no state rollback'
echo 'PASS: 0041 Step 10 dedicated production incremental cycle complete'
