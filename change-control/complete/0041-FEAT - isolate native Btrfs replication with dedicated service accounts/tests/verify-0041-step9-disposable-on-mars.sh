#!/usr/bin/env bash
# 0041: isolated Btrfs stream fixture on mars/backup using existing admin SSH.
# Does NOT exercise new forced-command receiver's receive operation; that is
# deliberately hard-bound to production state and cannot safely target fixtures.
# Execute as a standalone noninteractive root shell on mars.
set -Eeuo pipefail
umask 077
[[ ${EUID} -eq 0 ]] || { echo 'FAIL: requires root on mars' >&2; exit 1; }
export LC_ALL=C
stamp="$(date -u +%Y%m%dT%H%M%SZ)-$$"
[[ "$stamp" =~ ^[0-9]{8}T[0-9]{6}Z-[0-9]+$ ]] || exit 1
SRC="/media/usb/.0041-disposable-${stamp}"
DST="/@data/mars-received/.0041-disposable-${stamp}"
[[ "$SRC" == /media/usb/.0041-disposable-* && "$DST" == /@data/mars-received/.0041-disposable-* ]] || exit 1
SSH=(sudo -n -u richard ssh -T -o BatchMode=yes -o ConnectTimeout=15 -o StrictHostKeyChecking=yes -p 39263)
created_src=0
created_dst=0

remote() { "${SSH[@]}" -n richard@10.254.22.1 "sudo -n bash -c $(printf '%q' "$1")"; }
# Use standard privileged existing richard transport for isolated Btrfs-only
# fixture. Never use the production receiver-gate against these fake snapshots.
remote_receive() { "${SSH[@]}" richard@10.254.22.1 "sudo -n btrfs receive '$DST'"; }

safe_cleanup() {
  original=$?
  trap - EXIT
  local cleanup_error=0 name
  echo '=== Dispose of ONLY the newly created 0041 fixture subvolumes ==='
  if (( created_dst )); then
    for name in interrupted child parent; do
      if remote "test -e '$DST/$name'"; then
        remote "test ! -L '$DST/$name' && btrfs subvolume show '$DST/$name' >/dev/null && btrfs subvolume delete '$DST/$name'" || cleanup_error=1
      fi
    done
    remote "rmdir '$DST'" || cleanup_error=1
  fi
  if (( created_src )); then
    for name in interrupted child parent work; do
      if [[ -e "$SRC/$name" ]]; then
        if [[ -L "$SRC/$name" ]] || ! btrfs subvolume show "$SRC/$name" >/dev/null 2>&1; then
          echo "REFUSED: unexpected fixture entry $SRC/$name" >&2
          cleanup_error=1
        else
          btrfs subvolume delete "$SRC/$name" || cleanup_error=1
        fi
      fi
    done
    rmdir "$SRC" || cleanup_error=1
  fi
  if (( cleanup_error )); then
    echo "FAIL: fixture cleanup incomplete. Inspect ONLY $SRC and $DST; do not run a generic prune." >&2
    exit 1
  fi
  if (( original != 0 )); then
    echo "FAIL: isolated transfer verification failed (exit $original); fixture cleanup completed" >&2
  else
    echo 'PASS: disposable fixture cleanup completed'
  fi
  exit "$original"
}
trap safe_cleanup EXIT

echo "0041 STEP 9 DISPOSABLE BTRFS SEND/RECEIVE: $(date -u +%FT%TZ)"
echo "SOURCE_HOST=$(hostname) FIXTURE_TAG=$stamp"
echo 'SCOPE: only newly-created, unmanaged .0041-disposable-* directories'
echo 'NOTE: uses existing richard transport; dedicated forced-command is tested separately'
[[ "$(findmnt -n -T /media/usb -o FSTYPE)" == btrfs ]] || { echo 'FAIL: source not Btrfs' >&2; exit 1; }
[[ "$(remote 'findmnt -n -T /@data/mars-received -o FSTYPE')" == btrfs ]] || { echo 'FAIL: destination not Btrfs' >&2; exit 1; }
if systemctl is-active -q btrfs-native-push.service; then
  echo 'FAIL: source push currently running' >&2; exit 1
fi
if remote 'systemctl is-active -q btrfs-receiver-simple-prune.service'; then
  echo 'FAIL: receiver prune currently running' >&2; exit 1
fi

source_state='/media/usb/@snapshots/.simple-agreed-parent.json'
recv_state='/@data/mars-received/.replication-state/.simple-agreed-parent.json'
src_before="$(sha256sum "$source_state" | awk '{print $1}')"
dst_before="$(remote "sha256sum '$recv_state'" | awk '{print $1}')"
[[ "$src_before" =~ ^[0-9a-f]{64}$ && "$dst_before" =~ ^[0-9a-f]{64}$ ]] || exit 1

echo '=== Create isolated Btrfs fixture ==='
mkdir -m 0700 -- "$SRC"
created_src=1
remote "mkdir -m 0700 -- '$DST'"
created_dst=1
btrfs subvolume create "$SRC/work"
printf '0041 fixture parent\n' > "$SRC/work/value.txt"
btrfs subvolume snapshot -r "$SRC/work" "$SRC/parent"

echo '=== Full binary Btrfs send/receive ==='
btrfs send "$SRC/parent" | remote_receive
src_uuid="$(btrfs subvolume show "$SRC/parent" | awk '/^[[:space:]]*UUID:/{print $2;exit}')"
dst_received="$(remote "btrfs subvolume show '$DST/parent'" | awk '/^[[:space:]]*Received UUID:/{print $3;exit}')"
[[ -n "$src_uuid" && "$dst_received" == "$src_uuid" ]] || { echo 'FAIL: full-transfer received UUID mismatch' >&2; exit 1; }
echo 'PASS: full-transfer received UUID matched'

printf '0041 fixture child\n' > "$SRC/work/value.txt"
btrfs subvolume snapshot -r "$SRC/work" "$SRC/child"
echo '=== Incremental binary Btrfs send/receive ==='
btrfs send -p "$SRC/parent" "$SRC/child" | remote_receive
src_uuid="$(btrfs subvolume show "$SRC/child" | awk '/^[[:space:]]*UUID:/{print $2;exit}')"
dst_received="$(remote "btrfs subvolume show '$DST/child'" | awk '/^[[:space:]]*Received UUID:/{print $3;exit}')"
[[ -n "$src_uuid" && "$dst_received" == "$src_uuid" ]] || { echo 'FAIL: incremental received UUID mismatch' >&2; exit 1; }
local_digest="$(sha256sum "$SRC/child/value.txt" | awk '{print $1}')"
remote_digest="$(remote "sha256sum '$DST/child/value.txt'" | awk '{print $1}')"
[[ "$local_digest" == "$remote_digest" ]] || { echo 'FAIL: incremental payload checksum mismatch' >&2; exit 1; }
echo 'PASS: incremental received UUID and payload checksum matched'

echo '=== Interrupted stream then guarded fixture retry ==='
dd if=/dev/urandom of="$SRC/work/binary.dat" bs=1048576 count=4 status=none
btrfs subvolume snapshot -r "$SRC/work" "$SRC/interrupted"
if ( set -o pipefail; btrfs send -p "$SRC/child" "$SRC/interrupted" | head -c 128 | remote_receive ) >/dev/null 2>&1; then
  echo 'FAIL: intentionally truncated stream was unexpectedly accepted' >&2
  exit 1
fi
echo 'PASS: truncated stream rejected'
if remote "test -e '$DST/interrupted'"; then
  # Never delete an unexpected read-only/received snapshot. The interrupted
  # test name is unique and was absent before this test started.
  state="$(remote "btrfs subvolume show '$DST/interrupted'")"
  if printf '%s\n' "$state" | grep -Eq '^[[:space:]]*Flags:[[:space:]]*readonly'; then
    echo 'FAIL: interrupted candidate unexpectedly read-only; manual review' >&2
    exit 1
  fi
  remote "btrfs subvolume delete '$DST/interrupted'"
fi
btrfs send -p "$SRC/child" "$SRC/interrupted" | remote_receive
src_uuid="$(btrfs subvolume show "$SRC/interrupted" | awk '/^[[:space:]]*UUID:/{print $2;exit}')"
dst_received="$(remote "btrfs subvolume show '$DST/interrupted'" | awk '/^[[:space:]]*Received UUID:/{print $3;exit}')"
[[ -n "$src_uuid" && "$dst_received" == "$src_uuid" ]] || { echo 'FAIL: interrupted retry UUID mismatch' >&2; exit 1; }
echo 'PASS: interrupted fixture successfully resent and UUID verified'

echo '=== Confirm production agreed-parent records did not change ==='
[[ "$(sha256sum "$source_state" | awk '{print $1}')" == "$src_before" ]] || { echo 'FAIL: source agreed-parent changed' >&2; exit 1; }
[[ "$(remote "sha256sum '$recv_state'" | awk '{print $1}')" == "$dst_before" ]] || { echo 'FAIL: receiver agreed-parent changed' >&2; exit 1; }
echo 'PASS: production agreed-parent files unchanged'
echo 'PASS: isolated binary transfer, incremental send, interruption/retry verified'
