# 0034-FEAT - Make production complete-backup repository Btrfs-aware

## Type

Feature

## Status

In progress

Step progress (2026-10-08): **Step 1 CLOSED; Step 2 CLOSED** (five Playbooks regression suites and non-destructive `pluto` preflight passed). Step 3 is next. See `evidence/Step 2/CLOSEOUT.md`. 

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
- automatically use reflink-aware creation where the configured repository really supports it, while retaining an explicit full-copy path elsewhere;
- provide an explicit operating mode so a repository which is *expected* to be Btrfs fails rather than silently consuming full-copy space;
- cooperate with the existing Btrfs/Snapper and Synology snapshot layers without redefining a filesystem snapshot as a Diaries application backup;
- use timestamp-oriented Diaries backup identities and provide a timestamp-friendly operational view of filesystem snapshots without renaming Snapper's internal numeric snapshot IDs;
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
- define long-term off-site replication or a single cross-platform deletion engine beyond what is needed to prove safe deletion of shared backups;
- replace Snapper on `mars`/`backup` or Synology Snapshot Replication on the NAS;
- rename Snapper's internal numeric snapshot directories or make Diaries depend on those IDs;
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


### Reflink semantics

A recursive reflink clone is logically a **per-regular-file clone**, even though the implementation should normally invoke one recursive command rather than loop over every file in shell code. For example:

```bash
cp -a --reflink=always \
    "$base/files/." \
    "$candidate/files/"
```

`cp` walks the directory tree. For each regular file it asks Btrfs to clone the source file's extents into a new file. The two files have separate directory entries and separate inodes, but unchanged data extents are initially shared.

Conceptually:

```text
old/files/img0001.jpg ──┐
                        ├── shared extent A
new/files/img0001.jpg ──┘
```

This is deliberately **not a hard link**. If the candidate copy is changed, Btrfs copy-on-write allocates new extents for the changed data and the previous completed backup remains unchanged. If either backup is deleted, shared extents remain allocated while any surviving file still references them.

The implementation should use `--reflink=always` when it has selected reflink mode. `--reflink=auto` would be too easy to misinterpret operationally because a failed clone could silently become a full physical copy.

Reflinking is only an efficient way to seed the new candidate. It is never proof that the candidate is correct; the existing 0033 path/size/SHA-256 verification remains the correctness gate.

## Repository Configuration

Production must have an explicit complete-backup repository root configured through Playbooks rather than relying on an implicit assumption that `~/projects/diaries/data/dataset-backups/production` is on a particular filesystem.

The effective configuration must distinguish:

```text
live mutable Files root
production complete-backup repository root
production complete-restore state root
```

The complete-backup repository must remain outside the live mutable Files tree.

### Storage mode

Define an explicit complete-backup storage mode. The implementation may refine the exact variable name, but the contract should be equivalent to:

```yaml
diaries_complete_backup_storage_mode: auto
```

Supported values:

```text
auto
required-btrfs
full-copy
```

Semantics:

- `auto` — inspect the actual configured repository; use reflink-aware seeding when Btrfs/reflink capability is proven, otherwise use the normal 0033 full-copy path;
- `required-btrfs` — require the repository to be Btrfs and to pass the reflink probe; fail closed if either condition is false rather than silently consuming full-copy space;
- `full-copy` — deliberately disable reflink seeding and use the existing complete physical-copy path even when the repository is Btrfs. This is also the rollback/test mode.

For a production repository deliberately provisioned as Btrfs, `required-btrfs` is preferred. `auto` is useful for portable/local deployments where the same command should work on either Btrfs or non-Btrfs storage.

### Capability detection

Do not infer capability solely from a directory name, mount path or even a filesystem-type check. Preflight should resolve the actual repository path and at minimum record/verify:

```text
resolved repository path
filesystem type for that path
reflink probe succeeds when reflink mode is requested
same-filesystem clone source/destination where required
available space / allocation information sufficient for the operation
```

A filesystem-type check such as:

```bash
findmnt -T "$BACKUP_ROOT" -no FSTYPE
```

should be followed by a small real clone probe equivalent to:

```bash
printf 'reflink-probe\n' > "$probe_source"
cp --reflink=always "$probe_source" "$probe_clone"
```

The probe must be created inside the configured repository (or another deliberately equivalent location on the same filesystem) so it tests the path actually used by backup creation. Probe artifacts must be removed safely afterwards.

## Backup Creation Strategy

The operator continues to invoke the same complete-backup command. Storage mode changes only how the candidate `files/` tree is seeded:

```text
                         backup-dataset.sh
                                |
                                v
                    inspect configured repository
                                |
               +----------------+----------------+
               |                                 |
      reflink mode selected                full-copy mode
      and capability proven                selected/required
               |                                 |
               v                                 v
       reflink seed from                     copy live Files
       previous valid backup                  physically
               |                                 |
               +----------------+----------------+
                                |
                                v
                   exact reconciliation / capture
                                |
                                v
                  normal schema-2 verification
                                |
                                v
                      atomic promotion
```

In every mode the published object is a logically complete schema-2 backup. Restore cannot tell, and must not need to tell, which creation path was used.

### First complete backup

When no suitable previous completed backup exists for the same logical dataset, create the candidate Files snapshot using the normal verified full-copy path from 0033, even when the repository itself is Btrfs.

The first backup therefore remains valid even though it cannot benefit from an earlier reflink base. A subsequent backup can then use it as a reflink seed.

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

## Relationship to Existing Btrfs / Snapshot Protection

The existing infrastructure already has a second, lower-level recovery layer:

- `mars` and `backup` use Btrfs with Snapper-managed timeline snapshots and cleanup;
- the Synology NAS uses its native Btrfs/Snapshot Replication facilities;
- those mechanisms retain many recent filesystem states and progressively fewer older states according to their own retention policy.

0034 must cooperate with that infrastructure but must not collapse the two concepts into one.

The boundary is:

```text
Diaries complete backup = verified application recovery point
Btrfs/Snapper snapshot  = storage/filesystem recovery point
```

A Diaries backup deliberately couples a PostgreSQL dump with the exact Files tree, schema-2 manifest and verification evidence. A generic filesystem snapshot may be extremely useful for accidental deletion or rapid rollback, but by itself it does not replace the quiesced database + Files consistency contract established by 0033.

Therefore completed Diaries backups remain timestamp-named ordinary directories such as:

```text
20261007-145013Z/
20261008-020004Z/
20261009-021517Z/
```

They may live *inside* a Btrfs subvolume which Snapper also snapshots. In that arrangement the layers reinforce one another: the Diaries backup is independently restorable, while Snapper can additionally protect the repository against accidental deletion or corruption of recent repository state.

### Common retention philosophy, separate owners

The systems should use a common retention **vocabulary/philosophy** (dense recent history, progressively thinner old history) without introducing one script which directly deletes Snapper snapshots, Synology snapshots and Diaries application backups.

Conceptually a common policy vocabulary may describe buckets such as:

```text
keep-all / recent
hourly
daily
weekly
monthly
yearly
```

and map those intentions to each native owner:

```text
mars / backup -> Snapper cleanup policy
NAS           -> Synology Snapshot Replication / Smart Retention
Diaries       -> complete-backup retention policy
```

The exact counts do not have to be identical. Filesystem snapshots may sensibly be very dense for recent recovery, while verified application backups may be retained for a longer daily/weekly/monthly history.

A later retention feature may centralise the policy data or reporting, but native tools should remain responsible for deleting the objects they own.

### Snapshot naming and operator presentation

Diaries complete backups already use the preferred timestamp identity (`YYYYMMDD-HHMMSSZ`). Keep that as the canonical application-backup ID.

Snapper internally uses numeric snapshot IDs and its directory structure depends on them. Do **not** rename those snapshot directories merely to obtain friendlier names. Instead add or plan a small reporting/listing command which presents Snapper metadata in timestamp-first form while retaining the numeric ID internally, for example:

```text
DATE/TIME             HOST     CONFIG   ID    DESCRIPTION
2026-10-07 19:00Z     mars     @data    382   timeline
2026-10-07 18:00Z     mars     @data    381   timeline
```

Where useful, equivalent Synology snapshot timestamps should be presented in the same operator-facing view. This is presentation/operability work, not a change to snapshot identity.

## Retention and Deletion

Shared extents must not make operators afraid to remove old backups. Add a controlled test proving that deleting one completed backup does not alter or invalidate another backup that shared extents with it.

Deletion/retention tooling, if added, must:

- delete only complete-backup directories selected by an explicit retention decision;
- never delete `.partial` or restore-state evidence accidentally as a side effect of age sorting;
- never assume a newer backup depends logically on an older backup merely because extents are shared;
- revalidate at least one surviving backup after the deletion rehearsal.

A full automatic Diaries retention policy, and especially a single cross-platform deleter, is outside this feature unless separately approved. 0034 may, however, freeze the common retention vocabulary and timestamp-oriented reporting contract needed for later cooperative retention work.

Because Snapper/Synology snapshots can themselves retain references to extents belonging to a deleted Diaries backup, deleting an old application backup may not immediately reclaim all of its physical space. That is expected: Btrfs can reclaim an extent only after the final backup file *and* filesystem snapshot reference has disappeared. Operating documentation must explain this so delayed space reclamation is not mistaken for a failed deletion.

## Migration / Rollout

Existing completed schema-2 backups remain valid and require no conversion.

A safe rollout should be:

1. complete and close 0033;
2. inventory the current Snapper configuration/retention on `mars` and `backup` and record the corresponding Synology snapshot/retention configuration, without changing any of them yet;
3. define the common retention vocabulary and timestamp-oriented snapshot reporting contract;
4. provision or identify the production complete-backup repository;
5. configure the repository and explicit storage mode through Playbooks;
6. run filesystem/reflink capability preflight without changing backups;
7. create the first schema-2 backup in the repository using the normal full-copy path if no base exists there;
8. create a second backup using reflink-aware seeding when the configured mode/capability permits it;
9. validate both backups using the unchanged schema-2 validator;
10. prove unchanged Files share storage and changed Files remain correct;
11. rehearse deletion of one disposable/controlled backup and revalidate the survivor, noting that enclosing filesystem snapshots may legitimately delay physical space reclamation;
12. verify the full-copy path on non-Btrfs storage (or explicit `full-copy` mode);
13. update production operating documentation and close the feature.

Do not rewrite historical backup directories merely to manufacture sharing. They can age out under the normal retention process while new backups gain reflink sharing naturally.

## Detailed Implementation Steps

- [x] Freeze the current 0033 production backup path, schema-2 format and verification behaviour as regression evidence.
- [ ] Inventory and preserve the current Snapper configuration/retention on `mars` and `backup`, plus the corresponding Synology snapshot/retention settings where they can be recorded operationally.
- [ ] Decide whether the duplicated `remote-backup` snapshot setup should be refactored to the same parameterised snapshot role used by `mars`; keep that refactor separate from backup-media correctness if it would broaden deployment risk.
- [ ] Define a common retention vocabulary and timestamp-oriented snapshot-listing/reporting contract without creating a cross-platform deletion engine.
- [x] Define an explicit Playbooks variable/configuration contract for the production complete-backup repository root.
- [x] Define the `auto` / `required-btrfs` / `full-copy` storage-mode contract.
- [ ] Add preflight that resolves the repository, identifies its actual filesystem and performs a real `--reflink=always` capability probe whenever reflink mode is selected.
- [ ] Add regression coverage proving `dataset-manifest.json` remains schema version 2 with unchanged required semantics.
- [ ] Implement selection of the newest valid completed backup for the same logical dataset as the optional reflink base.
- [ ] Implement recursive reflink cloning of the previous `files/` snapshot into the new `.partial` candidate using per-file CoW cloning (`cp -a --reflink=always` or an equivalently proven mechanism), not hard links.
- [ ] Implement exact reconciliation of the cloned candidate against the quiesced live Files source, including add/change/delete behaviour and frozen `.image-staging` exclusion.
- [ ] Keep database dump creation, final Files SHA-256 verification, manifest generation/validation and atomic promotion unchanged in meaning.
- [ ] Add explicit operational output showing repository filesystem, optimisation mode and selected base backup.
- [ ] Test `auto`, `required-btrfs` and `full-copy` mode selection, including failure when `required-btrfs` is configured against an unsuitable repository.
- [ ] Test first-backup behaviour where no reflink base exists.
- [ ] Test repeated backup with no Files changes and prove substantial extent sharing/exclusive-space reduction.
- [ ] Test one changed large image, one new file and one deleted file between backups.
- [ ] Prove the previous completed backup remains byte-identical after candidate reconciliation.
- [ ] Prove deleting one extent-sharing backup does not invalidate another.
- [ ] Copy a completed optimised backup to non-Btrfs storage and validate it there using the ordinary schema-2 validator.
- [ ] Rehearse restore from Btrfs-backed media using the unchanged restore command/path.
- [ ] Add/verify a timestamp-first operator snapshot listing that preserves Snapper numeric IDs internally rather than renaming snapshot directories.
- [ ] Update Playbooks tests, production operator documentation and script classification under 0032.
- [ ] Record storage-efficiency evidence without making physical deduplication a correctness dependency.

## Acceptance Criteria

- [ ] Existing schema-2 backup layout and `dataset-manifest.json` semantics are unchanged.
- [ ] Existing schema-2 validation accepts Btrfs-aware backups without special cases.
- [ ] Restore requires no Btrfs-specific metadata or commands.
- [ ] Production repository identity is explicit and validated by Playbooks/tooling.
- [ ] Storage mode has explicit `auto`, `required-btrfs` and `full-copy` semantics.
- [ ] Capability is determined from the actual configured repository path, including a real reflink probe when reflink mode is selected; filesystem name alone is not treated as sufficient proof.
- [ ] `required-btrfs` fails closed if the repository is not Btrfs/reflink-capable; it never silently degrades to a full physical copy.
- [ ] `auto` uses reflink-aware seeding where capability is proven and otherwise produces a normal verified full-copy backup.
- [ ] The first backup with no suitable base succeeds using the defined full-copy path.
- [ ] A subsequent backup can reflink-seed from the newest valid completed backup for the same logical dataset.
- [ ] Recursive reflink seeding creates independent regular files/inodes which may share unchanged physical extents; hard links are not used.
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
- [ ] Documentation distinguishes a verified Diaries application recovery point from a generic Btrfs/Snapper/Synology filesystem recovery point.
- [ ] The retention design allows a common hourly/daily/weekly/monthly/yearly policy vocabulary while leaving deletion to the native owner of each backup/snapshot type.
- [ ] Operator-facing snapshot reporting can present timestamps while retaining Snapper's numeric IDs internally.
- [ ] Documentation explains that enclosing Snapper/Synology snapshots may delay physical-space reclamation after a Diaries backup directory is deleted.

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

### Risk: Btrfs is inferred but reflinks do not actually work at the configured path

Control: inspect the real repository filesystem and perform a small `--reflink=always` probe in that repository before selecting reflink mode.

### Risk: `auto` mode hides an unintended storage regression

Control: production repositories intentionally provisioned as Btrfs should use `required-btrfs`; operational output records the selected storage mode and whether reflink seeding was actually active.

### Risk: application backup and filesystem snapshot semantics become conflated

Control: preserve the schema-2 application backup as the authoritative database + Files recovery point and treat Snapper/Synology snapshots as an independent storage-protection layer.

### Risk: deleting an application backup appears not to free space

Control: document that reflink-shared extents and enclosing filesystem snapshots keep extents allocated until the final reference disappears; report exclusive/shared usage where practical.

## Deployment and Rollback

This is an operational-storage optimisation, not an application-data migration.

Rollback is to disable Btrfs-aware seeding and return backup creation to the existing 0033 full-copy path while continuing to use exactly the same schema-2 directory/manifest format. Existing Btrfs-aware backups require no conversion and remain valid restore media.

If the configured Btrfs repository itself becomes unavailable, normal production operation must remain unaffected; only complete-backup/restore operations that require that repository should fail explicitly.

## Step 3 progress (2026-10-08)

Capability preflight and explicit mode selection implemented; local regressions passed. Production preflight evidence and formal close-out remain pending. See `evidence/Step 3/README.md`. Reflink-based Files copying remains Step 4.
