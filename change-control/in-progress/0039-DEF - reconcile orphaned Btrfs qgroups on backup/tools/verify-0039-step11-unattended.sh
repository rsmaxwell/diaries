#!/usr/bin/env bash
# 0039-DEF Step 11: read-only evidence collection across scheduled cleanup days.
# Run from Windows Cygwin: bash <this-file> YYYY-MM-DD YYYY-MM-DD [more days]
# All persistent outputs remain inside the Windows Diaries feature tree.
set -euo pipefail

if (( $# < 2 )); then
  echo 'Usage: bash verify-0039-step11-unattended.sh YYYY-MM-DD YYYY-MM-DD [additional days]' >&2
  exit 2
fi
for day in "$@"; do
  if [[ ! "$day" =~ ^20[0-9]{2}-[01][0-9]-[0-3][0-9]$ ]]; then
    printf 'Invalid date argument: %s\n' "$day" >&2
    exit 2
  fi
done

feature_dir="$(cd "$(dirname "$0")/.." && pwd)"
evidence_dir="$feature_dir/evidence/Step 11"
mkdir -p "$evidence_dir"
log="$evidence_dir/unattended-$(date -u +%Y%m%d-%H%M%SZ).txt"

collect() {
  echo '=== 0039-DEF Step 11: read-only unattended cycles ==='
  date -u
  echo 'host=Windows Cygwin; target_hosts=mars,backup'
  echo '=== Diaries repository ==='
  (cd "$feature_dir/../../.." && git rev-parse --show-toplevel && git rev-parse HEAD && git status --short --branch) || return 1
  echo '=== Playbooks Git revision and changes (mango) ==='
  ssh mango 'cd /home/richard/playbooks && git rev-parse HEAD && git status --short --branch' || return 1

  for host in mars backup; do
    echo "=== $host: installed cleaner and scheduled timers ==="
    ssh "$host" 'sha256sum /usr/local/sbin/btrfs-clear-stale-qgroups' || return 1
    if [[ "$host" == mars ]]; then
      timers='btrfs-native-push.timer btrfs-clear-stale-qgroups.timer'
    else
      timers='btrfs-receiver-simple-prune.timer btrfs-clear-stale-qgroups.timer'
    fi
    for timer in $timers; do
      echo "--- $host: $timer ---"
      ssh "$host" "test \"\$(systemctl is-enabled '$timer')\" = enabled && test \"\$(systemctl is-active '$timer')\" = active" || return 1
    done

    for day in "$@"; do
      echo "=== $host: scheduled qgroup service on $day (UTC) ==="
      journal="$(ssh "$host" "sudo -n journalctl -u btrfs-clear-stale-qgroups.service --since '$day 05:20:00 UTC' --until '$day 06:30:00 UTC' --no-pager -o short-iso")" || return 1
      printf '%s\n' "$journal"
      # A success-shaped journal is mandatory for EACH requested day on EACH host.
      if ! printf '%s\n' "$journal" | grep -Eq "^${day}T.*[[:space:]]result=(complete|deferred_pending)([[:space:]]|$)"; then
        echo "FAIL: $host has no successful result=... on $day" >&2
        return 1
      fi
      if printf '%s\n' "$journal" | grep -Eq 'REFUSED|Failed with result|status=[1-9][0-9]*/FAILURE'; then
        echo "FAIL: $host has an error journal entry in $day window" >&2
        return 1
      fi
    done

    echo "=== $host: latest cleanup result ==="
    service="$(ssh "$host" 'sudo -n systemctl show btrfs-clear-stale-qgroups.service -p Result -p ExecMainStatus')" || return 1
    printf '%s\n' "$service"
    printf '%s\n' "$service" | grep -qx 'Result=success' || return 1
    printf '%s\n' "$service" | grep -qx 'ExecMainStatus=0' || return 1

    echo "=== $host: current cleaner classification (dry run only) ==="
    dryrun="$(ssh "$host" 'sudo -n /usr/local/sbin/btrfs-clear-stale-qgroups --config /etc/btrfs-stale-qgroups.json')" || return 1
    printf '%s\n' "$dryrun"
    printf '%s\n' "$dryrun" | grep -q 'dry_run=true' || return 1
    printf '%s\n' "$dryrun" | grep -q 'unmarked_orphans=0' || return 1

    echo "=== $host: snapshot-manager status (read only) ==="
    status="$(ssh "$host" 'sudo -n /usr/local/sbin/btrfs-snapshot-manager status')" || return 1
    printf '%s\n' "$status"
    printf '%s\n' "$status" | grep -q 'incomplete_timestamp_sets=0' || return 1
    if [[ "$host" == mars ]]; then
      printf '%s\n' "$status" | grep -q 'diaries_verification=valid' || return 1
    fi
  done

  echo '=== Both hosts: same installed shared cleaner SHA256 ==='
  mars_hash="$(ssh mars 'sha256sum /usr/local/sbin/btrfs-clear-stale-qgroups' | awk '{print $1}')" || return 1
  backup_hash="$(ssh backup 'sha256sum /usr/local/sbin/btrfs-clear-stale-qgroups' | awk '{print $1}')" || return 1
  [[ "${#mars_hash}" == 64 && "$mars_hash" == "$backup_hash" ]] || { echo 'FAIL: installed code hash mismatch' >&2; return 1; }
  printf 'PASS: installed cleaner sha256=%s\n' "$mars_hash"

  echo '=== Read-only simplified agreed-parent verification ==='
  sender="$(ssh mars 'sudo -n /usr/local/bin/btrfs-simplified-replication sender status')" || return 1
  receiver="$(ssh backup 'sudo -n /usr/local/bin/btrfs-simplified-replication receiver status')" || return 1
  python3 - "$sender" "$receiver" <<'PY'
import json,sys
s=json.loads(sys.argv[1]); r=json.loads(sys.argv[2])
assert s.get('relation')=='equal', 'sender relation is not equal'
assert s.get('receiver_parent_verified') is True, 'remote parent identity not verified'
p=s['state']['parent']
assert p==s['receiver']['parent']==r['state']['parent'], 'sender/receiver agreed-parent mismatch'
print('PASS: common parent timestamp='+p['timestamp']+' uuid='+p['uuid'])
PY
}

if collect "$@" 2>&1 | tee "$log"; then
  echo "PASS: 0039 read-only Step 11 evidence recorded at $log"
else
  echo "FAIL: 0039 Step 11 verification (partial log retained at $log)" >&2
  exit 1
fi
