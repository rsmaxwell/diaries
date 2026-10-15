# 0034-FEAT - Implementation Steps

Prepared 2026-10-08 from the completed 0033 complete-dataset backup/restore implementation, the updated 0034 design record, the current Diaries production Playbooks tooling, and the agreed separation between 0034 and 0035.

## Objective

Make the production complete-dataset backup repository **Btrfs-aware** without changing the schema-2 backup contract introduced by 0033.

A completed backup remains an ordinary, independently addressable directory:

```text
<backup-id>/
├── database/
│   ├── diaries.dump
│   └── diaries.sql
├── files/
├── verification/
└── dataset-manifest.json
```

On a proven Btrfs/reflink-capable repository, a new backup may seed its `files/` tree from the newest valid completed backup using recursive per-file reflink cloning. The candidate is then reconciled exactly against the quiesced live Files tree and must pass the unchanged 0033 path/size/SHA-256 verification before promotion.

On non-Btrfs storage, or when explicitly requested, the same command must continue to create a normal full physical copy.

Restore remains deliberately Btrfs-unaware.

## Working rules

1. The 0033 schema-2 directory layout, manifest semantics, validation rules, writer-quiescence behaviour and restore contract are frozen unless a change is explicitly justified by 0034.
2. Btrfs/reflink behaviour is an optimisation only. Backup correctness continues to be determined by the existing schema-2 validation and exact Files verification.
3. Never use hard links for backup seeding.
4. When reflink mode is selected, use a proven operation equivalent to `cp -a --reflink=always`; do not silently degrade through `--reflink=auto`.
5. Capability must be proven at the actual configured repository path. A filesystem name, mount name or directory convention alone is not sufficient.
6. A reflink base must be a completed, schema-2-valid backup for the same logical dataset. `.partial`, invalid, incomplete and cross-dataset media are never eligible.
7. The previous completed backup is immutable input. Candidate reconciliation must never modify it.
8. The first backup in an empty repository uses the normal full-copy path even when the repository is Btrfs.
9. The existing full-copy path remains permanently supported as fallback, explicit test mode and rollback.
10. `auto`, `required-btrfs` and `full-copy` must have distinct, testable semantics and explicit operator output.
11. Diaries complete backups remain application recovery points; Snapper/Synology snapshots remain filesystem recovery points. Do not merge their lifecycle or metadata models.
12. Do **not** deploy 0035 while implementing 0034. Existing Snapper protection on `mars`/`backup` remains unchanged until 0034 is complete, providing a stable independent storage-protection layer.
13. Do not require a destructive production restore merely to prove 0034. Use a disposable restored-production rehearsal for restore/portability proof.
14. Feature-only experiments and rehearsal tooling belong under 0034 evidence/tooling, not permanent live script directories, in accordance with 0032.

---

## Step 1 — Freeze the 0033 production backup contract and current storage baseline

Capture the exact pre-0034 production behaviour before changing repository selection or Files capture.

Freeze and record:

```text
current production complete-backup root
current backup command and preflight command
current schema-2 manifest example
current partial -> verified -> atomic-promotion behaviour
current database dump creation path
current Files full-copy implementation
current source-vs-backup path/size/SHA-256 verification
current responder quiescence and restart/fail-stopped behaviour
current restore path and repository assumptions
```

Run the existing permanent Playbooks regressions, including at minimum:

```bash
python3 roles/diaries/tests/verify-complete-dataset-manifest.py
python3 roles/diaries/tests/verify-production-backup-restore-semantics.py
python3 roles/diaries/tests/verify-production-complete-dataset-tooling.py
python3 roles/diaries/tests/verify-production-deployment-contract.py
python3 roles/diaries/tests/verify-production-storage-isolation.py
```

Record the current production filesystem identity for the existing backup root using commands such as:

```bash
findmnt -T <current-backup-root>
df -h <current-backup-root>
```

Do not relocate the repository in this step.

**Evidence:** baseline test output, current path/configuration, representative schema-2 manifest, current filesystem/mount evidence, relevant script fingerprints.

**Complete when:** pre-0034 behaviour is reproducibly frozen and any later difference can be attributed to 0034.

---

## Step 2 — Define the explicit repository-root and storage-mode configuration contract

**Status: CLOSED (2026-10-08).** Implementation, permanent regression tests and `pluto` non-destructive backup preflight passed. Evidence: `evidence/Step 2/CLOSEOUT.md`, `RUNTIME-MANGO-REGRESSIONS.txt`, `RUNTIME-PLUTO-PREFLIGHT.txt`. Step 3 remains outstanding.


Remove the implicit assumption that production complete backups always live beneath:

```text
~/projects/diaries/data/dataset-backups/production
```

Introduce a Playbooks-controlled production complete-backup repository root, while keeping the restore-state root distinct.

The effective configuration must separately identify:

```text
live mutable Files root
complete-backup repository root
complete-restore state root
```

Define the storage-mode contract equivalent to:

```yaml
diaries_complete_backup_storage_mode: auto
```

with exactly these supported semantics:

```text
auto
    use reflink-aware seeding only when the actual repository path proves
    Btrfs + reflink capability; otherwise use normal full copy

required-btrfs
    require Btrfs + successful reflink probe; fail closed otherwise

full-copy
    deliberately use the 0033 physical-copy path even on Btrfs
```

Decide how the deployed runtime receives the effective repository root and storage mode. Prefer a generated configuration/environment value over hard-coded paths inside Python.

Ensure repository and restore-state paths remain outside the mutable live Files tree.

Add static regression coverage for valid/invalid mode values and path separation.

**Evidence:** variable/configuration design, rendered example, static regression output.

**Complete when:** repository location and storage mode are explicit inputs to the production tooling and no backup code needs to infer them from project layout.

---

## Step 3 — Implement repository capability preflight and explicit mode selection

Extend production preflight so it resolves and reports the actual repository before any writer is stopped or backup workspace is created.

At minimum verify/report:

```text
resolved repository path
mount point
filesystem type
selected configured storage mode
effective backup strategy
free/allocation information
reflink capability when required
```

For reflink-capable operation, perform a real probe **inside the repository filesystem**, conceptually:

```bash
printf 'reflink-probe\n' > probe-source
cp --reflink=always probe-source probe-clone
```

Clean the probe safely afterwards.

Mode behaviour must be explicit:

```text
auto + successful Btrfs/reflink probe   -> effective strategy = reflink
auto + unsuitable repository            -> effective strategy = full-copy
required-btrfs + successful probe        -> effective strategy = reflink
required-btrfs + failed/unsuitable probe -> FAIL before writer quiescence
full-copy                                -> effective strategy = full-copy
```

Do not claim Btrfs optimisation if the actual clone probe was not successful.

Preflight must not create a complete backup, stop the responder, or mutate existing completed backups.

**Evidence:** preflight outputs for all three modes, intentional failed `required-btrfs` case, proof that no writer/storage media changed.

**Complete when:** strategy selection is deterministic, observable and fail-closed where required.

---

## Step 4 — Refactor Files capture behind a strategy-neutral candidate builder

Before adding reflinks, separate the current 0033 Files capture from the rest of `production-complete-dataset.py` so the orchestration can choose one of two candidate-building strategies without duplicating backup finalisation logic.

Conceptually:

```text
build Files candidate
    |
    +-- full-copy strategy   -> existing 0033 behaviour
    |
    `-- reflink strategy     -> added in later steps
```

The existing full-copy implementation must retain its current semantics:

```text
quiesced live Files source
    -> copy durable Files
    -> exclude .image-staging per frozen policy
    -> normalise host ownership as required
    -> independent source verification
```

Do not change:

```text
PostgreSQL dump creation
schema-2 manifest generation
source verification
manifest validation
atomic promotion
writer restoration/fail-stopped semantics
```

Add permanent regression proving `full-copy` mode produces media accepted by the unchanged schema-2 validator and behaves equivalently to the 0033 baseline.

**Evidence:** source diff/design note, permanent regression output, synthetic/full-copy candidate comparison.

**Complete when:** full-copy behaviour passes unchanged while Files candidate construction is ready for a second strategy.

---

## Step 5 — Implement safe reflink-base discovery and validation

Implement selection of an optional reflink base from the configured repository.

Candidate bases must be considered only if they are normal completed backup directories. Reject:

```text
.<backup-id>.partial
restore-state directories
non timestamp-shaped directories
missing manifests
invalid schema-2 manifests
incomplete backups
backups for another logical dataset
backups missing files/
backups whose recorded Files component fails validation
```

From the remaining valid backups, select the newest valid completed backup for the same logical dataset.

Do not trust directory-name ordering alone: a timestamp-shaped directory is not a valid base until its media validates.

If no valid base exists:

```text
auto/required-btrfs -> create this backup using full-copy seeding
```

This is the normal first-backup behaviour, not an error.

Record the selected base backup ID/path in operator output/evidence only. Do not add Btrfs-specific base metadata to `dataset-manifest.json`.

**Evidence:** unit/regression cases covering valid newest base, invalid newest backup skipped, `.partial` ignored, wrong dataset ignored, no-base behaviour.

**Complete when:** the implementation can reliably select a safe base without altering any backup media.

---

## Step 6 — Implement recursive reflink seeding and exact live-source reconciliation

Implement the reflink strategy.

Seed the new `.partial/files/` candidate from the selected base using an operation equivalent to:

```bash
cp -a --reflink=always \
    "$base/files/." \
    "$candidate/files/"
```

The command may be implemented directly or through a helper, but the required semantics are:

```text
each regular file is a separate file/inode
unchanged extents may be shared
hard links are not used as the sharing mechanism
failure to reflink is an explicit failure once reflink strategy is selected
```

Then reconcile the candidate against the **quiesced** live Files source using exact replacement semantics:

```text
unchanged live file -> leave cloned file untouched where possible
changed live file   -> replace/update from live source
new live file       -> add from live source
removed live file   -> remove from candidate
.image-staging      -> excluded exactly as defined by 0033
```

Prefer a reconciliation mechanism that preserves reflink sharing for unchanged files. Do not blindly rewrite every candidate file after cloning.

After reconciliation, run the existing independent 0033 source-vs-candidate path/size/SHA-256 verification. That verification, not reflink state, decides correctness.

Fingerprint the base backup before and after the operation and prove it is unchanged.

**Evidence:** focused test tree containing unchanged/changed/new/deleted files, before/after base fingerprints, source/candidate exact verification.

**Complete when:** a reflink-seeded candidate exactly matches the current source while the previous completed backup remains byte-identical.

---

## Step 7 — Add storage observability and permanent regression coverage

Add permanent tests and operator output for the optimisation without changing schema-2 media.

Operational output should clearly show, where applicable:

```text
repository path
repository filesystem
auto/required-btrfs/full-copy configured mode
effective strategy
selected reflink base backup ID or 'none'
reflink probe result
final backup ID/path
logical Files bytes
Btrfs physical/shared/exclusive evidence where practical
```

Use Btrfs-native reporting such as `btrfs filesystem du` where useful, but do not make a specific storage saving part of the correctness contract.

Permanent regression must cover at least:

```text
schema-2 manifest remains unchanged
full-copy mode
successful auto -> reflink selection
successful required-btrfs -> reflink selection
auto fallback to full-copy
required-btrfs rejection
first backup/no base
valid newest-base selection
invalid/.partial/cross-dataset base rejection
reflink command failure
reconciliation failure
source verification failure
atomic-promotion failure
base backup immutability
```

No Btrfs path, extent ID, subvolume ID or base-backup relationship may leak into required schema-2 manifest semantics.

**Evidence:** permanent test results and representative operator output.

**Complete when:** all strategy/correctness boundaries are enforced by repeatable source-level tests.

---

## Step 8 — Run a disposable Btrfs end-to-end rehearsal

Before touching the production repository, exercise the complete implementation on a disposable Btrfs repository. This may use a deliberately provisioned test area on an appropriate Linux host, but it must not interfere with 0035's undeployed snapshot-manager paths or existing Snapper-owned snapshots.

Rehearse:

1. empty Btrfs repository;
2. first complete backup -> full-copy seeding;
3. second backup with no Files changes -> reflink seeding;
4. prove materially shared storage/exclusive-byte reduction;
5. alter a controlled test Files source with:
   - one changed large file;
   - one new file;
   - one deleted file;
6. create the next backup and prove exact contents;
7. prove earlier backups remain byte-identical;
8. delete one controlled extent-sharing backup and revalidate a survivor;
9. copy a completed optimised backup to a non-Btrfs filesystem and validate it with the ordinary schema-2 validator;
10. run the unchanged restore path against disposable media/dataset and prove restore is Btrfs-unaware;
11. exercise `full-copy` mode on the same implementation;
12. exercise a deliberately unsuitable repository and prove `required-btrfs` fails before writer quiescence/media creation.

If enclosing Snapper/Synology snapshots are present, record that they can legitimately delay physical space reclamation after deletion; do not interpret that as failed backup deletion.

**Evidence:** full transcripts, manifests, hashes, Btrfs usage reports, before/after inventories, deletion-survivor proof, non-Btrfs validation and disposable restore proof.

**Complete when:** all 0034 storage and portability invariants have been demonstrated without production-risking changes.

---

## Step 9 — Provision and configure the production Btrfs repository

Identify or provision the real production complete-backup repository only after Step 8 passes.

Do not assume that the current `pluto` project filesystem, a CIFS path, `mars`, `backup` or the NAS automatically satisfies the reflink contract. The selected design must prove the backup process can perform local reflink operations at the actual configured path.

Record:

```text
repository host/path
mount source
filesystem type
Btrfs filesystem identity
ownership/permissions
capacity/free-space information
how the repository is made available to production tooling
storage mode (normally required-btrfs for an intentionally provisioned Btrfs repository)
restore-state path and separation from backup media
relationship to existing Snapper/Synology protection
```

Provision through Playbooks where appropriate. Deployment must create/validate the repository but must **not** automatically run a complete backup or delete/move historical backups.

Existing completed schema-2 backups require no conversion and should not be rewritten merely to manufacture sharing.

**Evidence:** Ansible/preflight output, filesystem/reflink proof, rendered effective configuration, path/permission evidence.

**Complete when:** production tooling sees an explicit, writable, reflink-capable Btrfs repository and no production backup has yet been changed or created by the deployment.

---

## Step 10 — Deploy 0034 tooling non-destructively and run production preflight

Deploy the final scripts/configuration through the Diaries Playbooks while keeping application images unchanged.

Run permanent Playbooks regression before and after deployment.

On production run only preflight first, verifying:

```text
logical dataset = production
correct database identity
correct Files selector/root
correct repository root
filesystem = btrfs
configured mode = required-btrfs (unless a deliberate alternative is documented)
reflink probe = success
current responder state reported but not changed
no .partial workspace created
no completed backup created/deleted/modified
```

Verify that existing database-only backup commands remain unchanged.

**Evidence:** deployment transcript, regression output, production preflight transcript, before/after repository inventory.

**Complete when:** the deployed production tooling is ready to use reflinks but has not yet performed a production complete backup.

---

## Step 11 — Create and validate the first production backup in the Btrfs-aware repository

Create the first complete production backup in the configured repository under the normal 0033 writer-quiescence rules.

If the repository contains no suitable valid base, the expected effective Files strategy is:

```text
full-copy (no valid reflink base)
```

The backup must still complete as ordinary schema-2 media.

Capture/verify:

```text
backup ID
repository/mode/effective strategy
writer quiescence and prior-state restoration
both PostgreSQL dumps
schema-2 manifest
Files path/size/SHA-256 exact match
no .image-staging leakage
final atomic promotion
post-backup responder health
Btrfs logical/exclusive usage baseline
```

Do not manufacture a fake base by copying/reflinking historical backups into the new repository.

**Evidence:** complete production backup transcript, manifest/verification results, health result, Btrfs usage baseline.

**Complete when:** one real production schema-2 backup exists in the Btrfs repository and validates using the unchanged 0033 validator.

---

## Step 12 — Prove successive production reflink backup, document operation and close 0034

Create a second real production complete backup after Step 11. With the first backup now available as a valid base, the expected strategy is:

```text
reflink
```

Prove:

```text
newest valid same-dataset base selected
recursive reflink seed succeeded
candidate reconciled against current quiesced Files source
previous backup fingerprint unchanged
new backup exact path/size/SHA-256 match
schema-2 manifest unchanged in format/meaning
atomic promotion succeeded
prior responder-running state restored
both completed backups independently validate
unchanged Files materially share Btrfs storage
```

Use `btrfs filesystem du` or equivalent evidence to distinguish apparent/logical size from exclusive/shared physical usage.

Do **not** delete a valuable production backup solely to repeat the deletion test already proven in Step 8. Production retention remains a separate operational decision.

Update operating documentation to cover:

```text
repository path and Playbooks variables
auto / required-btrfs / full-copy
first-backup versus subsequent-backup behaviour
reflink semantics and why they are not hard links
base-selection rules
verification/fail-closed behaviour
apparent versus shared/exclusive Btrfs usage
deleting backups with shared extents
interaction with enclosing Snapper/Synology snapshots
why restore remains Btrfs-unaware
full-copy rollback procedure
relationship to future 0035 snapshot-manager deployment
```

Classify all scripts under the 0032 managed-script policy. Archive/remove feature-only rehearsal tooling from live script directories.

Run final permanent regressions and record the final production state. Move 0034 from `in-progress` to `complete` only when every acceptance criterion in `README.md` is either evidenced or explicitly resolved.

**Evidence:** second production backup transcript, both manifest validations, base fingerprint proof, Btrfs shared/exclusive usage, final regression results, documentation inventory and close-out record.

**Complete when:** production is demonstrably using Btrfs-aware schema-2 complete backups, the ordinary full-copy path remains supported, restore remains unchanged, and 0034 is formally closed.

---

## Expected permanent implementation surface

The exact file split may evolve during implementation, but permanent changes are expected primarily under the Playbooks Diaries role, for example:

```text
roles/diaries/defaults/main.yaml
roles/diaries/tasks/*.yaml
roles/diaries/templates/.env.j2                 # if effective runtime config is carried here
roles/diaries/files/sync/scripts/backup-dataset.sh
roles/diaries/files/sync/scripts/production-complete-dataset.py
roles/diaries/files/sync/scripts/README.md
roles/diaries/README.md
roles/diaries/tests/
```

A small dedicated helper for repository capability/base selection/reconciliation is acceptable if it improves testability. If added, it becomes permanent only if it represents supported runtime behaviour; feature-only probes/rehearsals belong under 0034 evidence/tooling.

No Angular client, `diaries-web`, responder Java code, MQTT protocol or Docker image change is expected.

## Feature-level completion gate

0034 is not complete merely because `cp --reflink=always` succeeds. Close only when all of the following are true:

```text
0033 schema-2 media contract unchanged
repository root explicit
storage mode explicit
actual repository capability proven
first-backup full-copy behaviour proven
successive reflink backup proven
changed/new/deleted Files reconciliation proven
previous backup immutability proven
source path/size/SHA-256 verification unchanged and passing
invalid/.partial/cross-dataset bases rejected
full-copy fallback/rollback retained
non-Btrfs portability proven
disposable restore with unchanged restore tooling proven
deleting shared test media does not invalidate survivors
production operating documentation updated
0032 script hygiene satisfied
0035 still not required for correctness
```
