# 0032-FEAT - Clean up completed-feature verification tooling from live script directories

## Type

Feature

## Status

Complete — 2026-10-03

## Priority

Medium

## Opened

2026-10-03

## Implementation progress

- **Step 1 complete — 2026-10-03:** the Diaries and Playbooks snapshots plus the exact deployed `pluto` scripts directory have been inventoried under `evidence/Step 1`. The 60-file candidate table remains 40 `ARCHIVE`, 19 `PROMOTE/RENAME`, and 1 `PENDING`. The 23-file production inventory is fully explained by the current Playbooks deployment model; there are no unexplained stale scripts. All seven 0031 production helpers are byte-identical to source. The only sync-source/deployment drift is `scripts/README.md`, documented as non-executable documentation drift. No live file was moved, renamed or deleted.
- **Step 2 complete — 2026-10-03:** all 60 candidates now have an approved final disposition: 43 `ARCHIVE` and 17 `PROMOTE/RENAME`, with no pending decisions. `migration0024ImageCatalogue.sh` is explicitly classified as completed 0024 migration tooling and will be archived under 0024 rather than promoted as supported administration. The Windows and Playbooks `verify-0031-step16.py` aggregation gates are historical; lasting behavioural coverage is carried by neutral promoted validators. The archive layout is frozen across completed 0031, 0026 and 0024 evidence, and the exact eight-file production removal list is recorded under `evidence/Step 2`. No live file was moved, renamed or deleted.
- **Step 3 complete — 2026-10-03:** all 45 source versions requiring historical preservation now have byte-identical archive copies (43 final `ARCHIVE` candidates plus the two mixed validators that will later be promoted under neutral names) under the approved completed 0031, 0026 and 0024 evidence/tooling locations. Per-file provenance and SHA-256 are recorded under `evidence/Step 3`; supplied source-bundle hashes are used as source identity because the bundles contain no `.git` metadata. Historical feature records were not rewritten, bulky runtime evidence was not duplicated, and no live script/test was moved, renamed or deleted.
- **Step 4 complete — 2026-10-03:** the Windows cleanup/verification script ran successfully on the real checkout. The seven completed 0031 step directories and eight historical validators are no longer live, fourteen permanent validators/helpers use behaviour-oriented names, the exact Windows dataset-pair and direct-development runtime checks passed, all retained Python checks passed, and the three renamed Node helper suites passed. The generated Step 4 evidence is the authoritative Windows after-state.
- **Step 5 complete — 2026-10-03:** the atomic Playbooks cleanup patch was applied to the authoritative `/home/richard/playbooks` checkout. The role source now retains only supported database backup/restore/manifest tooling, live `verify-0031-*` coverage has been replaced with three behaviour-oriented production regressions, current operator documentation is feature-neutral, and Ansible contains the exact eight-name stale-script removal allow-list without `rsync --delete`. All three permanent validators passed with `python3` in the authoritative checkout and the Step 5-specific `git diff --check` is clean. No Playbooks deployment to `pluto` was performed; deployed cleanup is Step 6.
- **Step 6 complete — 2026-10-03:** the production cleanup was deployed through the guarded normal Diaries `--tags copy` path and verified on `pluto`. The three permanent Playbooks validators passed before deployment; Ansible removed exactly the eight approved obsolete helpers and completed with `failed=0`, `unreachable=0`, exit code `0`. Fresh pre/post evidence proves the permanent production script set is intact, retained operational helpers have the approved hashes and executable modes, `.env`, `compose.yaml` and responder configuration fingerprints plus non-secret database/Files selectors are unchanged, and all five required Diaries services are running and healthy. The portable verifier finished with `PASS: Step 6 production cleanup evidence verified.`
- **Step 7 complete — 2026-10-03:** permanent anti-accumulation protection is now active in both source trees. Diaries adds `verify-live-script-policy.py`, which enforces the supported `scripts/windows` top-level areas, rejects unclassified feature/step-shaped tooling, supports exact documented permanent exceptions, and is invoked by the normal `verify-dataset-pair-guard.py` safety regression. The Playbooks production deployment-contract regression continues to enforce the exact supported synchronized script set and now also detects feature/step-shaped helpers with a synthetic recurrence case. Reusable change-control plus Windows/production operator documentation now requires script classification at feature close-out and explicitly requires temporary production helpers to be deployed and removed deliberately. All targeted Step 7 guards and permanent source regressions passed; no production deployment or data mutation was performed.
- **Step 8 complete — 2026-10-03:** final before/after inventories and the 60-row disposition are reconciled with no pending candidate. The Windows host runner passed the permanent Windows/storage/backup guards, all 11 Node tests, responder/web Gradle tests (`BUILD SUCCESSFUL`) and the Angular production build. The `mango` host runner passed all three permanent Playbooks validators and native `ansible-playbook --syntax-check diaries.yaml`. All 11 acceptance criteria PASS. Step 6 remains the authoritative clean `pluto` production after-state; Step 7's managed-`scripts/` refinement needs no additional production mutation for close-out. 0032 is complete and its record is moved to `change-control/complete/`.


## Summary

Remove completed-feature migration, verification and evidence-capture tooling from the normal Diaries development and production script directories, while preserving enough source and evidence to reproduce or understand the completed work.

The end state should make the normal script directories answer a simple question:

> Is this script still supported for normal operation, administration, deployment or regression protection?

If the answer is no, the script should not remain in an operator-facing or automatically deployed script directory merely because an earlier feature needed it.

0031-FEAT exposed the problem clearly. Development now contains several `0031-step*` directories, while production currently deploys multiple `stepN-...` migration/control scripts directly into the main production `scripts` directory. Those files were useful while 0031 was being implemented, but leaving them indefinitely makes later work harder to understand and increases the risk of an obsolete migration helper being run against a newer system.

This feature is a source/tooling hygiene change. It must not alter Diaries application data, the PostgreSQL schema, mutable Files contents, retained MQTT state or the established database/Files isolation contract.

## Motivation

Feature implementation has produced three distinct kinds of scripts:

1. **Permanent operational tooling**
   - normal start/stop/status/log/shell commands;
   - supported backup/restore commands;
   - permanent administrative helpers required by the current architecture.

2. **Permanent regression or safety tooling**
   - guards which protect current invariants;
   - repeatable source/application tests which should continue to run after the originating feature is complete.

3. **Historical feature tooling**
   - one-off migration helpers;
   - feature-step evidence capture;
   - reconciliation wrappers used only during a completed migration;
   - preflight/postflight helpers whose purpose ended when the feature closed.

These categories are currently mixed together. 0032 will make the distinction explicit and establish a convention for future features.

## Source Areas in Scope

### Windows/development

Review:

```text
scripts/windows/
scripts/windows/validation/
```

In particular, 0031 left feature-step directories such as:

```text
scripts/windows/0031-step8/
scripts/windows/0031-step9/
scripts/windows/0031-step10/
scripts/windows/0031-step11/
scripts/windows/0031-step12/
scripts/windows/0031-step13/
scripts/windows/0031-step16/
```

The first six are present in the source bundle used to open this feature; `0031-step16` was added during the final 0031 close-out work.

These directories contain migration/evidence tooling rather than normal day-to-day launch commands.

### Production / Playbooks

Review:

```text
roles/diaries/files/sync/scripts/
roles/diaries/tests/
roles/diaries/tasks/copy.yaml
```

The normal Ansible `sync/` tree is copied into the production project. At the time this feature was opened, the production script source includes:

```text
backup-db-to-binary.sh
backup-db-to-sql.sh
dataset-backup-manifest.py
migration0024ImageCatalogue.sh
restore-db-from-binary.sh
restore-db-from-sql.sh
step8-capture-production-database-backup.sh
step8-freeze-writes.sh
step9-reconcile-production.sh
step12-compare-reconciliation.py
step12-reconcile-production.sh
step13-capture-production-control.sh
step14-production-deployment.sh
```

The `step8` through `step14` files are specifically 0031 migration/verification tooling. Because the role currently synchronizes `sync/` without `--delete`, removing them from the role source alone would not remove already-deployed copies from `pluto`.

## Classification Policy

Every script touched by this feature must be classified before it is moved or removed.

| Classification | Long-term location |
| --- | --- |
| Permanent operational/admin command | Normal supported script directory |
| Permanent safety/regression check | Stable validation/test location, preferably named for the behaviour it protects |
| Completed-feature migration/evidence tool | Completed change-control evidence/tooling archive, not a normal script directory |
| Unclear | Keep temporarily and record the decision as pending; do not delete merely for tidiness |

Feature numbers and step numbers are useful in historical evidence. They are usually a warning sign in permanent operator tooling.

## Proposed 0031 Development Disposition

The following directories are candidates to leave the live Windows script tree:

```text
scripts/windows/0031-step8/
scripts/windows/0031-step9/
scripts/windows/0031-step10/
scripts/windows/0031-step11/
scripts/windows/0031-step12/
scripts/windows/0031-step13/
scripts/windows/0031-step16/
```

Before removal:

1. inventory every file and every current reference to it;
2. confirm that the completed 0031 evidence already contains the necessary scripts, or preserve byte-identical copies under the completed feature evidence;
3. update historical READMEs/runbooks so archived commands point to the archived tooling rather than a live script path where appropriate;
4. remove the feature-step directories from `scripts/windows`;
5. prove normal development, local Docker and smoke-mode operation does not reference them.

The exact archival location should be consistent, for example:

```text
change-control/complete/
  0031-FEAT - isolate mutable Files storage by database environment/
    evidence/
      tooling/
        windows/
          step8/
          step9/
          ...
```

Do not duplicate large runtime evidence merely to move scripts. Preserve only the source/tooling that is needed for historical reproducibility.

## Proposed Permanent Windows Tooling

The following are examples of tooling that should remain live because it protects or operates the current system:

```text
scripts/windows/common/validate-dataset-pair.*
scripts/windows/common/resolve-effective-dataset.ps1
scripts/windows/common/report-effective-dataset.bat
scripts/windows/common/write-db-backup-manifest.ps1
scripts/windows/common/verify-db-backup-manifest.ps1

scripts/windows/development-infrastructure/*
scripts/windows/local-docker-build/*
scripts/windows/local-published-smoke/*
```

Individual files still require review; this list describes the intended category, not an unconditional keep decision.

## Windows Validation Cleanup

The `scripts/windows/validation` directory contains useful permanent regression coverage as well as feature/step-specific verification.

Review `verify-0031-*` tests and divide them into:

- **behavioural regression tests which remain valuable** after 0031;
- **historical structural tests** which only prove that a completed 0031 step/tool exists.

For permanent tests, prefer behaviour-oriented names such as:

```text
verify-storage-isolation.py
verify-backup-restore-semantics.py
verify-files-path-contract.py
```

rather than keeping a growing permanent list of `verify-0031-stepN.*` tests.

A historical test which only asserts the existence or exact shape of retired Step 8/9/13/16 tooling should be archived with the feature tooling instead of remaining in the normal validation suite.

Do not rename a test merely for appearance: first identify every caller and update the regression entry points atomically.

## Proposed 0031 Production Disposition

The following production files are candidates for archival/removal from the normal deployed `scripts` directory:

```text
step8-freeze-writes.sh
step8-capture-production-database-backup.sh
step9-reconcile-production.sh
step12-reconcile-production.sh
step12-compare-reconciliation.py
step13-capture-production-control.sh
step14-production-deployment.sh
```

Preserve the final source versions as historical 0031 tooling before deleting them from:

```text
roles/diaries/files/sync/scripts/
```

and from the deployed production project.

The production archive may be held with the completed 0031 evidence, for example:

```text
change-control/complete/
  0031-FEAT - isolate mutable Files storage by database environment/
    evidence/
      tooling/
        production/
          ...
```

Git history remains authoritative for the original Playbooks commits; the evidence copy exists to keep the completed feature self-contained and understandable.

## Production Scripts Expected to Remain

The 0031 storage model introduced ongoing operational behaviour which must not be removed merely because 0031 is complete.

The following are expected to remain unless review finds a better replacement:

```text
backup-db-to-binary.sh
backup-db-to-sql.sh
restore-db-from-binary.sh
restore-db-from-sql.sh
dataset-backup-manifest.py
```

They implement the supported database-only backup/restore semantics and the durable database + Files pairing safeguards used after 0031.

## `migration0024ImageCatalogue.sh` Decision

`migration0024ImageCatalogue.sh` needs an explicit decision rather than automatic removal.

If Image catalogue reconciliation remains a supported administrative operation, promote it to a permanent feature-neutral command, for example:

```text
reconcile-image-catalogue.sh
```

and update documentation/callers accordingly.

If it is only historical migration tooling for 0024/0031, preserve it with the relevant completed-feature evidence and remove it from the normal production script directory.

The feature must record which decision was made and why.

## Removing Stale Production Copies

The current Diaries role uses `ansible.posix.synchronize` for the `sync/` tree without `--delete`.

Therefore:

```text
remove file from role source
```

does **not** imply:

```text
remove already-deployed file from pluto
```

0032 must explicitly remove the known obsolete production files from:

```text
{{ diaries_project_dir }}/scripts
```

Step 6 did this with a narrowly scoped Ansible `state: absent` list. Step 7 subsequently makes the production `scripts/` directory itself a dedicated managed tree, so future stale entries are removed by a scripts-only synchronize task using `--delete` and `--delete-excluded`.

Do **not** add unrestricted `rsync --delete` to the whole Diaries project sync tree. The project-root synchronize task must exclude `scripts/`; destructive synchronization is permitted only on the dedicated production scripts directory, where the complete permanent static source set and protected templated script set are known.

After deployment, capture the resulting production script directory and prove that retired feature-step helpers are absent while supported operational scripts remain.

## Convention for Future Feature Tooling

Future feature-specific tooling should not be added permanently to a normal live script directory.

### Development

Prefer one of:

```text
change-control/in-progress/<feature>/tooling/windows/
```

or another clearly non-operational feature-tooling directory.

If the tool becomes a supported long-term command, promote it deliberately into the normal script tree and give it a behaviour-oriented name.

### Production

Feature-only production tooling should live outside the always-synchronized production script tree in source control.

When temporary deployment is required:

1. deploy only the named helper explicitly;
2. place it in a clearly feature-scoped temporary/tooling location;
3. record where it was deployed;
4. remove it as part of feature close-out;
5. verify removal.

A future feature must not rely on “we will remember to clean that up later”.

## Preventing Recurrence

Add permanent source checks which fail if a completed-feature pattern is introduced into a live script tree without an explicit allow-list.

Examples worth protecting include:

```text
scripts/windows/NNNN-step*/
roles/diaries/files/sync/scripts/stepN-*
```

The guard should not blindly reject every number in a filename; it should enforce the documented policy and permit deliberately supported commands where necessary.

Also update the change-control feature template/guidance so close-out includes:

> Classify every script introduced by the feature as permanent operational tooling, permanent regression tooling, or historical feature tooling. Archive/remove historical tooling from live script directories and, where applicable, verify that deployed copies have also been removed.

## Detailed Implementation Steps

- [x] Capture an exact inventory of Windows, Playbooks-source and deployed-production script directories before cleanup.
- [x] Find every source/documentation/test reference to each 0031 feature-step script.
- [x] Classify every candidate as permanent operational, permanent regression/safety, historical feature tooling, or pending decision.
- [x] Preserve any missing 0031 historical development tooling under completed change-control evidence.
- [x] Remove archived `scripts/windows/0031-step*` directories from the normal Windows script tree.
- [x] Review `scripts/windows/validation/verify-0031-*` and retain/rename only behaviour-oriented permanent regression coverage.
- [x] Preserve the retired production Step 8/9/12/13/14 helpers with completed 0031 evidence.
- [x] Remove retired 0031 production helpers from `roles/diaries/files/sync/scripts`.
- [x] Decide whether `migration0024ImageCatalogue.sh` is promoted to a supported feature-neutral reconciliation command or archived.
- [x] Review `roles/diaries/tests/verify-0031-*` and retain/rename only permanent behavioural regression coverage.
- [x] Remove the known stale deployed copies from `pluto`; Step 7 subsequently replaces the one-off removal list with scoped managed-`scripts/` synchronization, without applying `--delete` to the project-root sync.
- [x] Update development and production script READMEs so they document only supported live commands plus the new feature-tooling convention.
- [x] Add regression guards preventing completed-feature tooling from silently accumulating in live script trees.
- [ ] Run the remaining host-capable Java/Angular/Ansible final regression gates after the portable/source checks.
- [x] Deploy the production cleanup non-destructively and capture the final `pluto` script-directory inventory.
- [x] Confirm normal backup/restore, start/stop/status and storage-pair safeguards remain available.
- [ ] Close 0032 with an inventory of what was retained, renamed, archived and removed after the final host gates pass.

## Acceptance Criteria

- [x] `scripts/windows` contains no completed 0031 `0031-step*` operator directories.
- [x] `roles/diaries/files/sync/scripts` contains no retired 0031 `stepN-*` migration/control scripts.
- [x] `pluto` contains no stale deployed copies of the retired production helpers.
- [x] Supported start/stop/status/log/shell, backup/restore and storage-safety commands remain present and documented.
- [x] Every removed script has either an archived evidence copy or a documented reason why Git history alone is sufficient.
- [x] Permanent regression coverage protects current behaviour rather than the existence of retired feature steps.
- [x] The disposition of `migration0024ImageCatalogue.sh` is explicit and documented.
- [x] No database rows, PostgreSQL schema, mutable Files bytes or MQTT retained state are changed by cleanup.
- [ ] Full relevant Diaries and Playbooks regression checks pass after the cleanup — portable/source checks pass; Java/Angular/Ansible host gates remain.
- [x] A permanent guard/convention makes future completed-feature script accumulation detectable.
- [x] Feature close-out records an exact before/after script inventory for development, Playbooks source and production.

## Out of Scope

0032 does not:

- reopen or change the acceptance decision for 0031;
- repeat the 0031 database/Files migration;
- change database/Files mappings;
- change Image lifecycle semantics;
- remove historical evidence merely to save disk space;
- delete arbitrary production files by enabling global `rsync --delete`;
- redesign the application or deployment architecture beyond the tooling-placement policy needed to prevent recurrence.

## Dependencies

Requires 0031-FEAT to be complete.

The 0024/0030 Image catalogue lifecycle should be consulted only for the `migration0024ImageCatalogue.sh` disposition. No data migration dependency is introduced.

## Deployment and Rollback

The production portion is a non-destructive source/script cleanup.

Before deployment:

1. record the exact production script directory;
2. preserve the final retired helper sources in change-control evidence;
3. confirm the explicit Ansible removal list contains only known retired files.

After deployment:

1. list the production script directory again;
2. prove retired helpers are absent;
3. prove supported operational commands remain;
4. run normal status/read-only verification.

Rollback does not require database or Files restoration. If a removed script is unexpectedly still required, restore that script from Git/evidence and reclassify it before continuing. Do not restore the entire old script directory wholesale.
