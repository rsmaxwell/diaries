#!/usr/bin/env bash
# Read-only cross-host acceptance check for 0043. Run in Windows Cygwin.
set -euo pipefail

feature='change-control/in-progress/0043-FEAT - centralise Btrfs maintenance schedules'
if [[ ! -d "$feature" ]]; then
  echo 'FAIL: run from the Windows Diaries parent repository root' >&2
  exit 2
fi
mkdir -p "$feature/evidence/Step 3"
log="$feature/evidence/Step 3/live-schedule-$(date -u +%Y%m%d-%H%M%SZ).txt"

check_timer() {
  local host="$1" unit="$2" on_calendar="$3"
  echo "=== ${host}: ${unit} ==="
  ssh "$host" "systemctl is-enabled '$unit' && systemctl is-active '$unit' && systemctl cat '$unit'" \
    | awk -v expected="OnCalendar=${on_calendar}" '
        /^enabled$/ {enabled=1}
        /^active$/ {active=1}
        $0==expected {calendar=1}
        END {if(enabled && active && calendar) print "PASS: enabled/active/calendar";
             else {print "FAIL: enabled="enabled " active="active " calendar="calendar; exit 1}}'
}

(
  echo '=== 0043: live schedule readback ==='
  date -u
  echo '=== Playbooks source revision ==='
  ssh mango 'cd /home/richard/playbooks && git rev-parse HEAD && git status --short --branch'

  check_timer mars diaries-pull.timer '*-*-* 01:30:00 UTC'
  check_timer mars btrfs-snapshot-create.timer '*-*-* *:00:00 UTC'
  check_timer mars btrfs-snapshot-prune.timer '*-*-* 04:15:00 UTC'
  check_timer mars btrfs-native-push.timer '*-*-* 03:30:00 UTC'
  check_timer mars btrfs-clear-stale-qgroups.timer '*-*-* 05:30:00 UTC'
  check_timer backup btrfs-receiver-simple-prune.timer '*-*-* 04:15:00 UTC'
  check_timer backup btrfs-clear-stale-qgroups.timer '*-*-* 05:30:00 UTC'

  echo '=== mars: bounded daily prune capacity ==='
  ssh mars 'systemctl cat btrfs-snapshot-prune.service' |
    grep -F -- '--max-delete 32'

  echo '=== Installed manager status ==='
  for host in mars backup; do
    echo "=== $host ==="
    ssh "$host" 'sudo -n /usr/local/sbin/btrfs-snapshot-manager status'
  done

  echo '=== Agreed parent state (read-only) ==='
  sender=$(ssh mars 'sudo -n /usr/local/bin/btrfs-simplified-replication sender status')
  receiver=$(ssh backup 'sudo -n /usr/local/bin/btrfs-simplified-replication receiver status')
  python3 - "$sender" "$receiver" <<'PY'
import json, sys
s = json.loads(sys.argv[1]); r = json.loads(sys.argv[2])
assert s.get('relation') == 'equal'
assert s.get('receiver_parent_verified') is True
assert s['state']['parent'] == s['receiver']['parent'] == r['state']['parent']
print('PASS: verified same protected parent', s['state']['parent']['timestamp'])
PY

  echo '=== Next systemd elapses ==='
  for host in mars backup; do
    echo "--- $host ---"
    ssh "$host" 'systemctl list-timers --all --no-pager \
      btrfs-snapshot-prune.timer btrfs-receiver-simple-prune.timer \
      btrfs-clear-stale-qgroups.timer'
  done
) 2>&1 | tee "$log" && result=0 || result=$?
if (( result == 0 )); then
  echo "PASS: 0043 read-only host acceptance; evidence=$log"
else
  echo "FAIL: 0043 host acceptance; evidence=$log" >&2
  exit "$result"
fi
