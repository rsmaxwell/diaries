# 0050 — Receiver-local Diaries history design and command contract

## Existing implementation boundaries

The installed `diaries-backup-history` uses `--config /etc/btrfs-snapshot-manager.json` by default, groups verified occurrences by `(logicalDataset, backupId)`, and derives identity from `dataset-manifest.json` plus a verified snapshot marker. `diaries-backup-status` invokes that history reader with `--json list` and presents a narrow app-data report. Current 0049 Ansible installs status on `mars` only; the source `snapshots` role installs the history reader and independent schema-2 verifier. Receiver config has `mode: receiver`, `sources: [{name: "@data", snapshot_directory: "/@data/mars-received/@data"}]` and `verification: {required: false}`.

**Critical invariant:** `btrfs-snapshot-manager.py` rejects `verification.required=true` in receiver mode. Do not make this change to enable history; it would break receiver retention/manager configuration.

## Proposed configuration contract

Extend the receiver manager JSON with a **reader-only** namespace, ignored by the Btrfs snapshot manager:

```json
{
  "mode": "receiver",
  "snapshot_root": "/@data/mars-received",
  "sources": [
    {"name": "@data", "snapshot_directory": "/@data/mars-received/@data"}
  ],
  "verification": {"required": false},
  "diaries_history": {
    "enabled": true,
    "source_name": "@data",
    "dataset_relative_path": "backup/pluto/diaries-backup",
    "marker_relative_path": "backup/.diaries-snapshot-verified.json",
    "manifest_tool": "/usr/local/lib/diaries-backup/complete-dataset-manifest.py"
  }
}
```

This is an **illustrative partial JSON structure**: actual manager template retains all current retention, locks, receiver state, holds and other required keys. Add only `diaries_history` and do not recreate/reset any state.

In the history reader, select `diaries_history` when `mode=receiver`, and select existing `verification` when in source mode. Require `enabled=true` for receiver history; validate every path, type, `source_name`, configured `snapshot_directory`, and manifest-tool absolute location. The receiver's `@data` snapshot directory must resolve to the approved path inside `/@data/mars-received` and must not follow an untrusted symlink outside it. For each occurrence under `snapshot_directory/<timestamp>`, constrain every resolved dataset/marker path to that occurrence. Receiver failures should never fall back to a remote query or source dataset.

The receiver data tree to inspect is:

```text
/@data/mars-received/@data/<timestamp>/
  backup/.diaries-snapshot-verified.json
  backup/pluto/diaries-backup/dataset-manifest.json
  backup/pluto/diaries-backup/...schema-2 contents...
```

The marker must have `state=verified-published`, `snapshotEligible=true`, the exact `datasetRelativePath`, matching `backupId` and `logicalDataset`, and `manifestSha256` equal to the computed manifest hash. These checks are **manifest-identity evidence**, not full-content verification. An explicitly invoked `verify` runs `/usr/local/lib/diaries-backup/complete-dataset-manifest.py verify --backup-dir RECEIVER_LOCAL_PATH`, checks exit status and reports failure; it must not write received snapshots.

## Operator CLI and output compatibility

| Invocation on `backup` | Contract |
| --- | --- |
| `sudo -n diaries-backup-status [--json] [--limit N]` | Host-local narrow app history summary; JSON schema, `health=healthy/degraded/error`, `latest/recent`, warnings and exit codes as on `mars` |
| `sudo -n diaries-backup-history list` | Grouped retained backup IDs, counts and timestamps, aligned text |
| `sudo -n diaries-backup-history --json list` | Same `backups` and `warnings` arrays; no non-JSON stdout |
| `sudo -n diaries-backup-history list --all` | All retained occurrences, including repeated backup IDs |
| `sudo -n diaries-backup-history show BACKUP_ID [--logical-dataset DATASET] [--snapshot TIMESTAMP]` | Receiver-local occurrence(s), paths and manifest digests |
| `sudo -n diaries-backup-history path BACKUP_ID [--logical-dataset DATASET] [--snapshot TIMESTAMP]` | Exactly one absolute **receiver-local** backup directory path |
| `sudo -n diaries-backup-history verify BACKUP_ID [--logical-dataset DATASET] [--snapshot TIMESTAMP]` | Actual full schema-2 verifier exit-status check on selected receiver-local data |

`diaries-backup-status` continues to return `0=healthy`, `1=degraded`, `2=error`. `diaries-backup-history` retains its existing `0=success`, `2=conflict/warning/request failure` contract. No silent fallback, no backup-ID truncation, no extra stdout for the `path` command, and no RPC/framing changes. Whether a backup is retained is determined **only** by the host-local snapshot inventory; listing it on `backup` does not assert it remains on `mars`.

## Receiver-only backup required behaviour

With fixture backup `production/RECEIVER_ONLY` in a valid received snapshot but absent from the source:

- `mars` grouped history: `RECEIVER_ONLY` absent.
- `backup` grouped history: `RECEIVER_ONLY` present, with correct occurrence count and timestamps.
- `backup path RECEIVER_ONLY`: points under `/@data/mars-received/@data/<timestamp>/...` (fixture uses a disposable equivalent root).
- `backup verify RECEIVER_ONLY`: invokes full verifier against *that* received dataset; success/failure is specific to receiver bytes, independent of source availability.

A backup with the same ID and logical dataset but **different manifest SHA-256 across received occurrences** must remain a conflict (not silently choose one). Missing/unreadable marker or manifest, broken symlink, unsafe path, truncated JSON or wrong marker identity must be warned/degraded. Empty received inventory must produce the same labelled empty table as `mars`, not falsely claim the source is empty.

## Safety and rollback

No changes to Btrfs send/receive, agreed parent/prior, holds, receipts, retention, timers, deletion caps, read-only state, or 0041 SSH/sudoers identity. Source snapshot-creation verification must still gate `mars` unchanged.

Rollback is an Ansible-controlled reversal of **reader executable/config additions only**, after capturing installed checksums, with the original receiver manager configuration preserved and all snapshots intact. If the extra config namespace itself causes unexpected parser/preflight behavior, immediately restore the prior receiver template and reapply; do not reset state. The source commands must remain working throughout.
