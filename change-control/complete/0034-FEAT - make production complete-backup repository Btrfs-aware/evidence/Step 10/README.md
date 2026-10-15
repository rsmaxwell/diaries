> **2026-10-11 supersession:** This file records the earlier prepared rsync receiver design and is retained as historical evidence. The current native `btrfs send`/`receive` Step 10.2 contract is `STEP-10.2-FROZEN-BTRFS-REPLICATION-CONTRACT.md`; do not run the rsync acceptance procedure below as the native transport.

# 0034-FEAT — Step 10 implementation and runtime evidence plan

**Status: IMPLEMENTATION PREPARED — RUNTIME ACCEPTANCE PENDING**  
**Prepared:** 2026-10-09  
**Order:** `mango` source regression → `mars` → `backup`  

## What changed in source

Step 10 necessarily hardens the prepared 0035 source before any live deployment. The supplied pre-Step-10 snapshot role still enabled native timers and disabled Snapper creation during ordinary role execution, had no verified receive/snapshot handshake and had no `diaries-backup-history`. Deploying that version unchanged would violate the revised 0034/0035 contract.

The Step 10 implementation now provides:

1. **Default-off migration controls.** `btrfs_snapshot_activation_enabled` and `btrfs_snapshot_snapper_handover_enabled` both default to `false`. Ordinary deployment installs/configures/preflights only. Snapper handover additionally requires verified-Diaries integration.
2. **Verified snapshot barrier.** Receivers and the snapshot manager share one whole-backup flock. Snapshot creation refuses a missing/stale marker and checks marker `logicalDataset`, `backupId`, fixed dataset path and manifest SHA-256 before taking a snapshot.
3. **Coordinated timestamp-set retention.** GFS retention is applied to complete timestamps across all configured snapshot sources. An incomplete `root`/`@data` set blocks pruning instead of allowing the two sources to drift independently.
4. **`mars` handoff.** The `pluto` pull remains staged; schema-2 verification precedes atomic receiving publication. Only then is `snapshotEligible=true` written. Known normal-user and root `mars` backup wrappers share the same writer lock.
5. **Read-only backup history.** `diaries-backup-history list`, `list --all`, `show`, `path` and `verify` operate only below manager-owned timestamp snapshots. Duplicate IDs are grouped by `(logicalDataset, backupId)`; incompatible repeated manifest identities are conflicts.
6. **`backup` pull.** An opt-in helper pulls from one explicit immutable `mars` `@data` snapshot. The local eligibility marker is invalidated before writable mirror mutation and recreated only after independent schema-2 verification and identity/hash agreement with the source snapshot marker.
7. **Extent-sharing proof.** `btrfs-extent-sharing` compares equal files in two retained snapshots using SHA-256 plus FIEMAP physical ranges, providing actual Btrfs sharing evidence instead of apparent-size inference.
8. **Controlled rollout material.** Playbooks `verification/0034-step10/README.md` and `capture-baseline.yaml` define the exact mars-first/backup-second acceptance procedure.

## Source evidence captured in the preparation workspace

Focused regressions passed for:

- native manager retention/timestamp namespace;
- default-off activation and Snapper handover;
- verified marker and writer-lock contract;
- complete timestamp-set retention;
- history duplicate grouping, conflict detection and symlink-escape refusal;
- `mars` staged receive and marker ordering;
- known `mars` writer locking;
- `backup` explicit-snapshot pull, pre-mutation marker invalidation, control-file exclusions and post-verify eligibility; and
- Python compilation of the four principal integration helpers.

YAML parsing passed for the changed defaults/tasks and Step 10 baseline playbook. The full established 0034 regression set must still be rerun on `mango`; a heavy pre-existing suite exceeded the local container execution budget and is not claimed as passed here.

## Runtime evidence still required

Do not close Step 10 until the following have been supplied and attached here:

- `mango` full source-regression transcript;
- `mars` predeploy scheduler/Snapper/subvolume baseline;
- non-activating `mars` deployment result and postdeploy scheduler comparison;
- first verified `pluto` pull and native snapshot;
- second native snapshot with the same Diaries ID and one-row/two-occurrence history proof;
- FIEMAP physical-extent sharing proof between the two `mars` snapshots;
- a newly published later `pluto` ID, new `mars` receive/snapshot, and full history verification of old and new IDs;
- `backup` baseline and proven SSH read path to `mars` native snapshots;
- non-activating `backup` deployment;
- controlled pull from an explicit verified read-only `mars` snapshot and local native snapshot;
- duplicate-history and physical-extent proof on `backup`; and
- confirmation that no failed/unverified receive can be advertised by history as a restorable verified snapshot.

## Scheduling boundary

Step 10 proves the controlled integration path. It does **not** itself authorise unattended timer activation or Snapper handover. Before that later 0035 gate, inventory every writer of the whole-backup trees. The known `mars` local jobs are now lock-aware, but any intermittent-device writers must be reconciled. On `backup`, the historical live `mars` push must be retired/replaced before the backup-host native schedule is activated.

**Decision:** source implementation is ready for `mango` regression and `mars` runtime acceptance. Step 10 remains OPEN pending live evidence.
