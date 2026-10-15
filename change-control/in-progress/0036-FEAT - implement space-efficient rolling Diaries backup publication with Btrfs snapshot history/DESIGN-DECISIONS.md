# 0036-FEAT — DESIGN DECISIONS AND OPEN QUESTIONS

## Agreed principles (2026-10-14)

1. Prefer a **constant logical backup path** on ext4 `pluto` over indefinitely retained timestamped full-copy directories.
2. Prefer a **single rolling current Btrfs dataset** on `mars`; timestamped read-only Btrfs snapshots supply history.
3. Preserve existing 0033 schema-2 layout and recovery verification, 0034 verified publication/pull/native replication, 0035 timestamp manager and retention protections.
4. Never assume equal-content independently copied files automatically share Btrfs extents; unchanged photo inodes/extents should not be rewritten on `mars`.
5. Preserve independent remote history and tested ability to restore an earlier dataset after newer changes or deletion.

## Choices to resolve during Steps 1–4 (not pre-decided)

- **Ext4 atomicity:** generation target + atomically renamed symlink versus journalled directory operation; how many ext4 rollback targets are retained, when may they be deleted, and how to prevent consumers observing partial writes.
- **Ext4 duplicate data during construction:** incremental `rsync --link-dest`/hard-link previous immutable file tree versus safer selective copies; hard links must never allow writes through to already published bytes. ext4 has no reflinks in this setup.
- **`mars` COW candidate:** writable snapshot clone of the accepted `@data` tree vs file-level reflink working tree. No new nested subvolumes that unexpectedly disappear from parent snapshots or native replication.
- **Marker placement:** where monotonic backup-ID state, verified manifest hash and stage journal live relative to mutable working dataset and immutable snapshot; distinguish acceptance receipt from mere file existence.
- **Verification scope:** manifest file checksums, DB integrity/restore, metadata-only changes and exact inode/extent evidence. Avoid relying solely on `rsync` mtime/size to decide correctness.
- **Return path to ext4:** if `mars` has failed after `pluto` switches, retain source rollback generation until durable accepted receiver acknowledgement.
- **Deletion and dataset isolation:** never permit sync to delete outside the selected logical dataset; preserve non-Diaries `@data` backup content and snapshot manager internals.
- **Historical migration:** old generated directories remain valid until separately reviewed; mappings from backup ID to physical Btrfs snapshot cannot depend on a deleted generation path.

## Explicit design rejection

A bare `rsync --inplace` directly onto the sole accepted writable dataset, followed by immediate deletion of old generation directories, is **not accepted**. It lacks the fail-safe transaction and recovery properties required here.
