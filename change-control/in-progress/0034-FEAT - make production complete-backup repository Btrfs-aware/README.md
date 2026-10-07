# 0034-FEAT - Make production complete-backup repository Btrfs-aware

## Type

Feature

## Status

To do

## Priority

Medium

## Opened

2026-10-07

## Summary

Make the production complete-dataset backup repository Btrfs-aware so successive Diaries backups can share unchanged filesystem extents instead of physically copying the same photographs into every backup directory.

The optimisation must be invisible to the complete-backup media contract introduced by 0033. Every completed backup must remain a normal, independently addressable schema-2 backup directory containing the same logical components and manifest semantics as before:

```text
<backup-id>/
├── database/
│   ├── diaries.dump
│   └── diaries.sql
├── files/
├── verification/
└── dataset-manifest.json
```

No schema-3 format is introduced by this feature. A restore must not need to know whether a backup was created using Btrfs reflinks, a normal copy, or was later copied to a non-Btrfs filesystem.

## Background

0033 adds complete database + Files backup and restore. The production Files tree contains large photographs, and successive backups are expected to contain a high proportion of identical file content. If every backup copies every photograph afresh, physical backup storage grows approximately with the apparent size of each Files snapshot even when little has changed.

Btrfs supports copy-on-write extent sharing. A new ordinary directory tree can be created as a reflink clone of the previous completed backup. Unchanged files then share their underlying extents; only changed/new file content and normal metadata consume additional physical storage. Deleting an older backup does not invalidate newer backups because Btrfs keeps shared extents until their final reference is removed.

The important distinction is:

```text
ordinary repeated copy      -> identical files usually consume new extents
Btrfs reflink clone + sync  -> unchanged files can continue sharing extents
```

The backup format itself does not need to change to gain this benefit.

## Goals

- keep the existing 0033 schema-2 backup directory and manifest contract unchanged;
- keep complete backups usable by the existing restore tooling without Btrfs-specific restore logic;
- use Btrfs copy-on-write sharing for unchanged Files content in successive production backups;
- preserve exact snapshot semantics: added, changed and deleted live Files must be reflected correctly in the new backup;
- keep `.partial` workspaces non-restorable and completed backups atomically promoted as defined by 0033;
- retain the existing independent SHA-256/path/size verification before promotion;
- make the Btrfs optimisation observable in operational output and testable without embedding storage-specific fields into `dataset-manifest.json`;
- keep the first backup and any deliberate non-Btrfs fallback behaviour well defined;
- keep database-only backup commands unchanged.

## Non-goals

This feature does not:

- change schema-2 `dataset-manifest.json`;
- introduce Btrfs-specific references, extent IDs, subvolume IDs or snapshot IDs into backup media;
- make restore depend on Btrfs;
- deduplicate the live mutable Files tree;
- silently run post-processing deduplication over unrelated filesystem data;
- change PostgreSQL dump formats;
- change the logical production database/Files pairing;
- define long-term off-site replication or retention policy beyond what is needed to prove safe deletion of shared backups;
- make completed backups writable application storage.

## Architectural Decision

Prefer **reflink-cloned ordinary directories**, not Btrfs subvolume snapshots, for the schema-2 backup media.

Conceptually:

```text
previous completed backup/files/
            |
            | cp --reflink=always (or equivalent proven reflink operation)
            v
new .<backup-id>.partial/files/
            |
            | exact reconcile from quiesced live Files source
            | add new files
            | replace changed files
            | remove files deleted since previous backup
            v
verified candidate -> atomic promotion -> completed backup
```

Reasons:

- the resulting backup remains an ordinary directory tree;
- the existing manifest does not need filesystem-specific metadata;
- moving/copying a backup to another filesystem materialises normal file contents and remains valid;
- existing restore code can continue to read `files/` without understanding Btrfs;
- backup deletion remains ordinary directory deletion from the operator's point of view;
- subvolume lifecycle and nested-subvolume deletion rules do not leak into the backup contract.

A later implementation may prove another Btrfs mechanism superior, but it must preserve all of these media and restore properties before replacing this decision.

## Repository Configuration

Production must have an explicit complete-backup repository root configured through Playbooks rather than relying on an implicit assumption that `~/projects/diaries/data/dataset-backups/production` is on a particular filesystem.

The exact variable name is an implementation decision, but the effective configuration must distinguish:

```text
live mutable Files root
production complete-backup repository root
production complete-restore state root
```

The complete-backup repository must remain outside the live mutable Files tree.

For Btrfs-aware mode, preflight must prove that the filesystem containing the backup repository supports reflinks. At minimum record/verify:

```text
resolved repository path
filesystem type = btrfs
reflink probe succeeds
same-filesystem clone source/destination where required
available space / allocation information sufficient for the operation
```

Do not infer Btrfs solely from a directory name or mount path.

## Backup Creation Strategy

### First complete backup

When no suitable previous completed backup exists for the same logical dataset, create the candidate Files snapshot using the normal verified full-copy path from 0033.

The first backup therefore remains valid even though it cannot benefit from an earlier reflink base.

### Subsequent complete backups

Select the newest **completed, schema-2-valid backup for the same logical dataset** as the reflink base.

Never use as a base:

- a `.<backup-id>.partial` workspace;
- a backup whose manifest does not validate;
- a backup for another logical dataset;
- a backup whose required Files component is missing or invalid;
- a directory that merely has a timestamp-shaped name but is not valid completed media.

Create the new candidate `files/` tree by reflink-cloning the previous completed `files/` tree. Then reconcile it against the quiesced live Files source using exact replacement semantics:

```text
unchanged live file -> leave cloned file/extents untouched where possible
changed live file   -> replace with current content
new live file       -> add
removed live file   -> delete from candidate
.image-staging      -> excluded according to the frozen 0033 staging policy
```

The reconciliation must not depend only on apparent directory equality. Final 0033 verification remains authoritative and must independently prove exact path/size/SHA-256 equality against the quiesced live source before promotion.

## Copy-on-write Safety Invariants

The implementation must prove these properties:

```text
modifying the new candidate never changes the previous completed backup
removing the previous completed backup never damages a newer backup
removing a newer backup never damages an older backup
changed files stop sharing the changed extents as required by CoW
unchanged files may remain extent-shared
backup validity is determined by schema-2 content/hashes, not by extent-sharing state
```

A backup must remain logically complete even if Btrfs later chooses different physical allocation or the backup is copied to another filesystem.

## Verification and Evidence

Keep the existing 0033 media verification unchanged as the correctness gate:

```text
custom PostgreSQL dump structurally valid
plain SQL dump readable
schema-2 manifest valid
Files path set exact
Files sizes exact
Files SHA-256 exact
logical dataset identity exact
partial/completed workspace semantics exact
```

Add separate Btrfs optimisation evidence outside the manifest, for example operator/test output showing:

```text
Btrfs repository detected
reflink base backup selected
reflink clone succeeded
candidate reconciliation succeeded
shared/extents or exclusive-byte evidence before/after
completed backup still validates with the normal schema-2 validator
```

Use Btrfs-native reporting such as `btrfs filesystem du` where appropriate to show that a second mostly-identical backup consumes materially less exclusive storage than a second full physical copy. Do not make a particular compression ratio or byte saving part of the backup correctness contract.

## Failure Semantics

Btrfs optimisation must never weaken 0033 fail-closed behaviour.

If any of the following occurs:

```text
repository is expected to be Btrfs but is not
reflink probe fails
base backup becomes invalid during preflight
reflink clone fails
candidate reconciliation fails
source verification fails
manifest validation fails
atomic promotion fails
```

then:

- the candidate remains non-restorable `.partial` media or is safely removed according to the existing policy;
- no completed backup is published;
- the previous completed backup remains untouched;
- writer-state restoration follows the existing 0033 rules;
- the failure is explicit in command output and logs.

Do not silently claim a Btrfs-optimised backup if the operation fell back to a normal full copy. If fallback is supported, it must be an explicit documented mode and must still produce valid schema-2 media.

## Restore Semantics

Restore remains deliberately **Btrfs-unaware**.

The existing 0033 restore path must continue to consume a backup only through its normal schema-2 content:

```text
database/diaries.dump
files/
dataset-manifest.json
verification metadata
```

Restore must work when the selected backup has been:

- left in the Btrfs repository with shared extents;
- copied to another Btrfs filesystem;
- copied to ext4/NTFS/other ordinary storage, thereby materialising independent file contents;
- archived and later rehydrated as normal files.

No restore preflight may require a particular Btrfs UUID, subvolume ID, generation number, extent ID or reflink relationship.

## Production and Playbooks Scope

Expected changes are primarily production operational tooling and Playbooks:

- introduce/configure the explicit production complete-backup repository root;
- validate Btrfs/reflink capability when Btrfs-aware mode is enabled;
- teach `backup-dataset.sh` / its helper to select a valid previous backup as a reflink base;
- perform reflink clone + exact live-source reconciliation;
- retain the existing 0033 final verification and atomic promotion;
- report which backup was used as the clone base and whether reflink optimisation was active;
- keep restore logic and database-only tooling compatible and unchanged unless path configuration requires a narrowly scoped update;
- update Ansible regression coverage and operator documentation.

No Angular client, diaries-web, MQTT RPC or responder application behaviour is expected to change.

## Retention and Deletion

Shared extents must not make operators afraid to remove old backups. Add a controlled test proving that deleting one completed backup does not alter or invalidate another backup that shared extents with it.

Deletion/retention tooling, if added, must:

- delete only complete-backup directories selected by an explicit retention decision;
- never delete `.partial` or restore-state evidence accidentally as a side effect of age sorting;
- never assume a newer backup depends logically on an older backup merely because extents are shared;
- revalidate at least one surviving backup after the deletion rehearsal.

A full automatic retention policy is outside this feature unless separately approved.

## Migration / Rollout

Existing completed schema-2 backups remain valid and require no conversion.

A safe rollout should be:

1. complete and close 0033;
2. provision or identify the production Btrfs backup repository;
3. configure the repository through Playbooks;
4. run Btrfs/reflink capability preflight without changing backups;
5. create the first schema-2 backup in the new repository using the normal full-copy path if no base exists there;
6. create a second backup using reflink-aware seeding;
7. validate both backups using the unchanged schema-2 validator;
8. prove unchanged Files share storage and changed Files remain correct;
9. rehearse deletion of one disposable/controlled backup and revalidate the survivor;
10. update production operating documentation and close the feature.

Do not rewrite historical backup directories merely to manufacture sharing. They can age out under the normal retention process while new backups gain reflink sharing naturally.

## Detailed Implementation Steps

- [ ] Freeze the current 0033 production backup path, schema-2 format and verification behaviour as regression evidence.
- [ ] Define an explicit Playbooks variable/configuration contract for the production complete-backup repository root.
- [ ] Add preflight that resolves the repository and proves Btrfs + reflink capability when Btrfs-aware mode is enabled.
- [ ] Add regression coverage proving `dataset-manifest.json` remains schema version 2 with unchanged required semantics.
- [ ] Implement selection of the newest valid completed backup for the same logical dataset as the optional reflink base.
- [ ] Implement reflink cloning of the previous `files/` snapshot into the new `.partial` candidate.
- [ ] Implement exact reconciliation of the cloned candidate against the quiesced live Files source, including add/change/delete behaviour and frozen `.image-staging` exclusion.
- [ ] Keep database dump creation, final Files SHA-256 verification, manifest generation/validation and atomic promotion unchanged in meaning.
- [ ] Add explicit operational output showing repository filesystem, optimisation mode and selected base backup.
- [ ] Test first-backup behaviour where no reflink base exists.
- [ ] Test repeated backup with no Files changes and prove substantial extent sharing/exclusive-space reduction.
- [ ] Test one changed large image, one new file and one deleted file between backups.
- [ ] Prove the previous completed backup remains byte-identical after candidate reconciliation.
- [ ] Prove deleting one extent-sharing backup does not invalidate another.
- [ ] Copy a completed optimised backup to non-Btrfs storage and validate it there using the ordinary schema-2 validator.
- [ ] Rehearse restore from Btrfs-backed media using the unchanged restore command/path.
- [ ] Update Playbooks tests, production operator documentation and script classification under 0032.
- [ ] Record storage-efficiency evidence without making physical deduplication a correctness dependency.

## Acceptance Criteria

- [ ] Existing schema-2 backup layout and `dataset-manifest.json` semantics are unchanged.
- [ ] Existing schema-2 validation accepts Btrfs-aware backups without special cases.
- [ ] Restore requires no Btrfs-specific metadata or commands.
- [ ] Production repository identity is explicit and validated by Playbooks/tooling.
- [ ] When Btrfs-aware mode is enabled, preflight proves the repository is actually Btrfs and reflink-capable.
- [ ] The first backup with no suitable base succeeds using the defined full-copy path.
- [ ] A subsequent backup can reflink-seed from the newest valid completed backup for the same logical dataset.
- [ ] Unchanged Files can share physical extents while the new backup remains a logically complete ordinary directory tree.
- [ ] Changed/new/deleted Files are represented exactly in the new backup.
- [ ] Final source comparison still proves exact paths, sizes and SHA-256 hashes before promotion.
- [ ] No `.partial`, invalid or cross-dataset backup can be used as a reflink base.
- [ ] Modifying a candidate cannot change a previous completed backup.
- [ ] Deleting either of two extent-sharing completed backups does not invalidate the survivor.
- [ ] Copying an optimised backup to non-Btrfs storage preserves a valid, restorable schema-2 backup.
- [ ] Database-only backup commands and semantics remain unchanged.
- [ ] No client, responder, diaries-web or MQTT protocol change is required.
- [ ] Production and regression tooling follows the 0032 managed-script hygiene rules.
- [ ] Documentation explains apparent size versus exclusive/physical Btrfs usage so operators do not mistake shared extents for missing backup data.

## Dependencies

Depends on 0033-FEAT being completed and its schema-2 backup/restore contract being frozen.

The production Btrfs repository must be provisioned/mounted before production rollout, but its exact host path is intentionally not assumed by this change record.

## Risks and Controls

### Risk: optimisation accidentally changes backup semantics

Control: keep schema-2 validation and final live-source SHA-256 comparison as the authoritative correctness gates. Reflink sharing is an implementation detail only.

### Risk: cloning from a damaged or wrong backup

Control: base candidates must be completed, schema-2-valid and for the same logical dataset before use.

### Risk: operators interpret apparent directory size as consumed disk space

Control: document and report both logical/apparent backup size and Btrfs exclusive/shared usage where practical.

### Risk: deleting an old backup appears to threaten newer backups

Control: document Btrfs extent reference semantics and preserve a deletion rehearsal proving survivor validity.

### Risk: repository silently stops being Btrfs

Control: production preflight validates filesystem type/reflink capability before claiming Btrfs-aware operation.

### Risk: a reflink-aware sync mutates the previous backup

Control: candidate is a separate reflink clone, never the previous backup directory; regression fingerprints the previous backup before and after candidate reconciliation.

## Deployment and Rollback

This is an operational-storage optimisation, not an application-data migration.

Rollback is to disable Btrfs-aware seeding and return backup creation to the existing 0033 full-copy path while continuing to use exactly the same schema-2 directory/manifest format. Existing Btrfs-aware backups require no conversion and remain valid restore media.

If the configured Btrfs repository itself becomes unavailable, normal production operation must remain unaffected; only complete-backup/restore operations that require that repository should fail explicitly.
