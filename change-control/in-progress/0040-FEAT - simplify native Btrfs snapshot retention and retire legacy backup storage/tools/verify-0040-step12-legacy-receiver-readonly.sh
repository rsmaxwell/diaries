#!/usr/bin/env bash
# 0040-FEAT read-only live receiver diagnostic; execute directly from mango Diaries root.
# No receive --accept, bootstrap, pruning, state mutation or service change.
set -euo pipefail
if [[ ${1:-} != --run ]]; then
  echo "Usage: bash '<0040-feature>/tools/verify-0040-step12-legacy-receiver-readonly.sh' --run" >&2
  exit 2
fi
cd /home/richard/diaries
FEATURE='change-control/in-progress/0040-FEAT - simplify native Btrfs snapshot retention and retire legacy backup storage'
LOG_DIR="$FEATURE/evidence/Step 12/raw-logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/step12-legacy-receiver-readonly-$(date -u +%Y%m%d-%H%M%S).txt"
# These exact candidate identities were logged by the legacy service on 6 November.
CANDIDATE=20261106-030016Z
CANDIDATE_UUID=18ad6ce8-d422-5142-9074-4583dd20bded
PARENT=20261101-140039Z
PARENT_UUID=69ef9a57-50ff-9a4e-92ed-8f10560ab1f2
run_checks() {
  echo '=== Host / repository provenance ==='
  hostname
  date -u --iso-8601=seconds
  git branch --show-current
  git rev-parse HEAD
  git status --short
  git submodule status

  echo '=== Receiver legacy transaction marker metadata: no contents or deletion ==='
  ssh -o BatchMode=yes backup sudo -n python3 - <<'PYTHON'
from pathlib import Path
from stat import S_IMODE
root = Path('/@data/mars-received/.replication-state')
for name in ('.agreed-parent-transfer-pending.json',
             '.receiver-prune-pending.json',
             '.agreed-parent-provisional.json',
             '.simple-agreed-parent.json',
             '.agreed-parent.json'):
    p = root / name
    if p.is_symlink():
        print('UNSAFE SYMLINK:', p)
    elif not p.exists():
        print('ABSENT:', p)
    else:
        st = p.lstat()
        print('PRESENT:', p, 'uid=', st.st_uid, 'mode=', oct(S_IMODE(st.st_mode)),
              'size=', st.st_size, 'bytes')
PYTHON

  echo '=== Legacy candidate: source Btrfs identity ==='
  ssh -o BatchMode=yes mars     "sudo -n btrfs subvolume show /media/usb/@snapshots/@data/$CANDIDATE"
  echo '=== Verified common parent: source ==='
  ssh -o BatchMode=yes mars     "sudo -n btrfs subvolume show /media/usb/@snapshots/@data/$PARENT"
  echo '=== Verified common parent: receiver ==='
  ssh -o BatchMode=yes backup     "sudo -n btrfs subvolume show /@data/mars-received/@data/$PARENT"

  echo '=== Actual mars-to-backup legacy receiver preflight: NO --accept ==='
  # Same SSH user, destination/port and arguments as failed scheduled push,
  # but the receiver's validate-only code path (not the receiving code path).
  if ssh -o BatchMode=yes mars     "sudo -n -u richard ssh -o BatchMode=yes -o ConnectTimeout=15 -p 39263 richard@10.254.22.1 '/usr/local/bin/btrfs-native-push-receiver --snapshot $CANDIDATE --source-uuid $CANDIDATE_UUID --parent $PARENT --parent-uuid $PARENT_UUID'"; then
    echo 'OBSERVED: legacy receiver validation accepted this request (no transfer performed)'
  else
    result=$?
    echo "OBSERVED: legacy receiver validation rejected this request (exit=$result)"
    echo 'Interpret the preceding error, not just the exit code; preserve any pending journal.'
  fi
  echo 'DONE: read-only legacy receiver diagnostic (NOT approval to bootstrap/cut over)'
}
run_checks 2>&1 | tee "$LOG"
echo "Evidence: $LOG"
