# Step 06 — Remaining operational acceptance checks

**Status: IN PROGRESS.** Execute from the existing **backup SSH terminal**, not mango. All commands are read-only (Python `-h` only; no verifier on dataset).

```bash
echo '=== Installed program sanity ==='
for script in /usr/local/sbin/btrfs-snapshot-manager /usr/local/sbin/diaries-backup-history /usr/local/lib/diaries-backup/complete-dataset-manifest.py; do
  sudo stat -c '%n owner=%U:%G mode=%a size=%s' "$script"
done
sudo /usr/local/sbin/diaries-backup-history --help
sudo python3 /usr/local/lib/diaries-backup/complete-dataset-manifest.py --help

echo '=== Native received snapshot identities and count ==='
sudo btrfs subvolume list / | grep 'mars-received/@data/'

echo '=== Replication receipt directory (metadata only) ==='
sudo find /@data/mars-received/.replication-state -maxdepth 2 -type f -printf '%P owner=%u:%g mode=%m bytes=%s\n' | sort
echo '=== Native receiver installed/configured entrypoints (read-only) ==='
sudo ls -ld /@data/mars-received/@data /@data/mars-received/.replication-state
sudo find /usr/local/sbin -maxdepth 1 -type f -name '*btrfs*native*' -printf '%f\n' | sort
```

For receipt **contents**, inspect only non-secret keys and identifiers after discovering the filenames; avoid uploading tokens or private keys. Confirm locally that recorded latest receive identifier matches a received subvolume and is consistent with native receiver metadata. The source bundle alone cannot prove these runtime relationships. Review findings before Step 6 closure.
# Step 06 — Operational verification (completed)

**CLOSED 21 October 2026.** Original read-only checklist satisfied using the operator's terminal outputs, not simulated execution.

- `note(20261020-203934).txt`: snapshot-manager status succeeds; `diaries_verification=disabled`; installed JSON lacks the obsolete writer lock and dataset path; three local snapshot timers disabled/inactive; original 14 receiver subvolumes present; replication-state directory accessible.
- `note(20261021-071157).txt`: installed manager, backup-history and schema-2 verifier are all `root:root`, mode `755`, and pass Python syntax compilation; 15 date-stamped receipts are `richard:richard` mode `600`, `writer.lock` exists, receiver metadata directory is `0700`.
- `note(20261021-071328).txt`: verified `20261021-030006Z` receipt against read-only Btrfs received subvolume ID `55805`; receipt `received_uuid` = Btrfs `Received UUID`, successful exit statuses and expected incremental parent; inventory contains all earlier 14 IDs and the new ID.

The optional `qgroups_status=unavailable;reason=unexpected_output` remains deferred. No forced off-site transfer or restoration was required. See `STEP06-ACCEPTANCE.md`.
