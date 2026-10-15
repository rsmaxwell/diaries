# Step 4 — Ratified source publication and replication contract

Status: **Design contract ratified; live rsync integration inventory remains a Step 6 prerequisite.** Date: 2026-10-08.

## Grounded starting point

- Production `production-complete-dataset.py` currently creates `<repository>/.<backupId>.partial`, independently verifies and validates the schema-2 dataset, then `os.replace(partial, repository/<backupId>)`. Existing timestamped directories remain immutable, valid restore inputs.
- Playbooks currently defaults `diaries_complete_backup_repository_root` to `{{ diaries_project_dir }}/data/dataset-backups/production`, restore state to `{{ diaries_project_dir }}/data/dataset-restores/production`, and mode to `auto`. `pluto` Step 3 preflight reported ext4, mode `auto`, effective `full-copy`.
- The supplied source bundles do **not** establish live `pluto → mars → backup` rsync commands, paths, service users, schedules, exclusions, locking or snapshot subvolume boundaries. These must be captured from those machines before Step 6 and 0035 activation; diagrams are not operational evidence.

## Frozen logical contract

- Stable external relative name: **`diaries-backup/`**; one current completed schema-2 dataset. The tree contains `database/diaries.dump`, `database/diaries.sql`, `files/`, `verification/`, `dataset-manifest.json` with unchanged 0033 component semantics.
- Immutable `backupId` and `logicalDataset` remain in manifest, not inferred from pathname. A new completed generation gets a new ID, even if most Files remain unchanged. Never change schema version, hashes, source dataset identity or restore safety checks for this feature.
- **Explicit new Playbooks input (to implement in Step 8):** `diaries_complete_backup_published_root` with an absolute path to the stable *external* `diaries-backup` directory. Default proposal: `{{ diaries_project_dir }}/data/diaries-backup`. This is deliberately **not** an alias for the Step 2 repository root: that continues to hold legacy `<backupId>/` entries during migration. Reject equality/overlap with restore-state and legacy repository roots, and with source Files root. Freeze the final deployed absolute path after verifying actual rsync source selection.
- Production still runs in full-copy mode on ext4. `required-btrfs` must fail clearly for any legacy invocation; do not repurpose it to mean downstream Btrfs. The Step 3 `reflink` selection/guard is obsolete for new publication and must be retired explicitly in Step 8, leaving historical tests/evidence intact.

## Publication protocol chosen for Step 5

1. A **private immutable generation directory** is created under a generation store on the *same ext4 filesystem* as the public pointer. Name by unique backup ID. Only a successfully verified schema-2 directory may become visible.
2. The public logical path `diaries-backup/` is a symlink to the selected immutable generation. Create a relative temporary symlink in the public directory's parent and atomically rename it over the preceding symlink (`os.replace`/`rename(2)`). **Never** use two sequential renames of ordinary non-empty current directories as an atomic switch. Ensure the parent and targets are on the same filesystem; use directory fsync for publication durability, with fail-safe behaviour where unsupported.
3. Use one documented advisory lock on `pluto` shared by the publisher's **handover/retirement operation** and the replication reader. Prefer `flock` on a persistent lock file outside the generation store, with a shared lock held by the reader from generation selection to transfer completion and an exclusive lock for switching/retiring. An equivalent tested generation lease may replace locking only through a documented contract amendment.
4. The reader must pin the resolved immutable generation while the lock is held; it must not follow the stable symlink afresh on each file operation. On failure the previous pointer remains usable. An earlier generation is not deleted while readers may hold it, and cleanup requires an explicit retention policy.
5. **Symlink semantics are a deployment gate:** check actual rsync flags and destination layout. The transfer must deliver the *contents* of a pinned generation as the real receiver `diaries-backup/` tree, not store a symlink to an inaccessible `pluto` generation path. Example only (not a live command): `rsync -a --delete -- "$PINNED_GENERATION/" "$RECEIVER_STAGING/diaries-backup/"`. Scope `--delete` to the managed tree, never the whole backup store. Do not use `--inplace` or `--append` with snapshot-backed receiving trees.
6. Receiver uses separately staged synchronization and schema-2 validation. Successful rsync alone cannot authorize a snapshot. 0035 accepts a successful validation handoff containing `backupId`, `logicalDataset`, source-generation identity and a receiver verified status, before snapshotting a coherent whole-backup mirror.

## Compatibility / transition

| Phase | Legacy `<backupId>/` | Public `diaries-backup/` | Restore | Rollback |
| --- | --- | --- | --- | --- |
| Current 0033 | Supported; current producer | Not available | Legacy ID/path | No change |
| Step 5 isolation | Preserved | Test-only | Legacy unchanged | Remove test publication |
| Step 9 opt-in | Preserved, not deleted | Verified current generation | Explicit legacy/fixed selection | Repoint to last-good generation or revert invocation/config; preserve all IDs |
| 0035 integrated | Historical readable | Replicated into verified whole-backup mirror | Snapshot source selected explicitly, destructive safeguards unchanged | Keep prior verified snapshots + legacy media |

Never make snapshot-manager installation or ordinary Ansible role deployment invoke a backup or change production data automatically.

## Must pass before Step 5/6 implementation acceptance

- Invalid manifest or interrupted producer cannot change the public pointer; failed second backup leaves first accessible.
- Two completed generations have unique IDs, are independently schema-2-valid, and are published in sequence without mixed contents.
- Concurrent rsync reader holds its pinned generation while new publication waits or preserves its lifetime; test handover on ext4 with actual `flock` and rsync options.
- Capture actual source and destination commands, users, timers, mount/subvolume identities, and full rsync exclusion/delete policy on `pluto`, `mars`, and `backup` **before production sync changes**.
- Receiving-side failure, checksum/manifest mismatch or interruption never becomes snapshot-eligible. Retain existing Snapper scheduling until 0035 safe activation gates are implemented and checked.

This Step 4 document is a design freeze, **not proof** of implementation, deployed settings, rsync orchestration, or production concurrency testing.
