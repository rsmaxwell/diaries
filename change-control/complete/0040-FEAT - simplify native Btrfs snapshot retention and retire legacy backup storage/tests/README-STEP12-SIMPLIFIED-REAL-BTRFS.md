# Step 12 — Simplified replication disposable real-Btrfs test

Purpose: independently exercise the **new simplified** `btrfs-simplified-replication.py`
against real Btrfs filesystems before activation. This is a one-off feature
acceptance test, not permanent Playbooks operational code.

## Safeguards and scope

- **Not an unattended service or deployment.** Nothing is installed on `mars` or
  `backup`; neither the 03:30 native push timer nor receiver pruning changes.
- Requires explicit `--run`, root, `btrfs-progs`, `mount`/`umount`, kernel Btrfs
  and loop-mount support. Without `--run` no file or mount is created.
- Uses two newly created 512 MiB sparse Btrfs image files in a unique
  `/var/tmp/0040-simplified-real-btrfs-*` directory on **mango**. `mkfs.btrfs`
  targets only these images; no physical devices or production mounts.
- Imports the simplified receiver implementation from the **current Playbooks
  checkout**, with receive path, state file, Btrfs filesystem UUID and lock
  redirected to the disposable fixture. No SSH to backup is made. The host
  checkpoint hold file is not modified. The isolated receiver fixture has no
  legacy pending transactions.
- On success the test unmounts both images and removes the directory. On
  failure it tries to unmount and preserves the fixture, explicitly printing
  its path. Inspect and clean it up intentionally after diagnosing a failure.

## Acceptance coverage

1. Creates source snapshots A and B, transfers A in full and verifies Btrfs
   received UUID and read-only state. Creates simple parent records at both
   ends in the fixture.
2. Creates a genuine incremental Btrfs send stream for B; truncates it and
   verifies that receive fails. If that particular btrfs-progs version has
   already removed the partial candidate, creates a disposable writable
   Btrfs subvolume as a simulated power-loss residue. The output explicitly
   distinguishes these scenarios.
3. Verifies receiver lock collision returns `DEFERRED` (exit 75), without
   progressing replication.
4. Runs the **actual simplified receiver CLI** in a local subprocess with
   the complete native stream. Verifies exact incomplete-subvolume deletion,
   receive retry, Btrfs identity and payload, and atomic receiver parent
   advancement.
5. Deliberately leaves sender state old (lost acknowledgement), invokes the
   simplified sender cycle against the fixture's receiver state, prohibits
   retransmission and checks both states and parent/prior pruning protection.

Limitations: does not establish SSH/sudo configuration, production filesystem
UUID constants, two-host service execution, unattended systemd operation or
receiver pruning. Source-level tests for these integration boundaries remain
relevant. Do not claim this as the complete Step 12 gate.

## Execute and preserve evidence

**Terminal: SSH to mango** (after the Diaries feature ZIP is applied and the
simplified Playbooks source is available at `/home/richard/playbooks`):

```bash
cd /home/richard/diaries

FEATURE='change-control/in-progress/0040-FEAT - simplify native Btrfs snapshot retention and retire legacy backup storage'
SCRIPT="$FEATURE/tests/verify-0040-step12-simplified-real-btrfs.py"
LOG="$FEATURE/evidence/Step 12/raw-logs/step12-simplified-disposable-real-btrfs-20261105.txt"
mkdir -p "$FEATURE/evidence/Step 12/raw-logs"

(
  printf 'Diaries revision: ' && git rev-parse HEAD &&
  printf 'Playbooks revision: ' && git -C /home/richard/playbooks rev-parse HEAD &&
  printf 'Playbooks local changes:\n' && git -C /home/richard/playbooks status --short &&
  sudo -n env PYTHONDONTWRITEBYTECODE=1 python3 "$SCRIPT" --run --playbooks /home/richard/playbooks
) > "$LOG" 2>&1
result=$?
cat "$LOG"
if [ "$result" -eq 0 ]; then
  echo 'PASS: simplified disposable real-Btrfs integration'
else
  echo 'FAIL: simplified disposable real-Btrfs integration'
fi
```

If the test reports a preserved fixture, **do not run another test or delete
that directory until the mounts and failure are understood**. Append results
and revision identifiers to the feature's evidence only after inspection.
