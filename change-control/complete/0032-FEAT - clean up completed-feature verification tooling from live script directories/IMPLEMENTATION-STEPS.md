# 0032-FEAT - Implementation Steps

Prepared 2026-10-03 from the 0032 feature definition, the completed 0031 change-control records, and the current Diaries/Playbooks script layout.

## Objective

Clean completed-feature migration, verification and evidence-capture tooling out of the normal Diaries development and production script directories without losing historical reproducibility or weakening permanent operational and regression safeguards.

The desired end state is:

```text
live script directories
    contain only
        supported operational/admin commands
        +
        permanent safety/regression tooling

completed-feature-only tooling
    lives with
        completed change-control evidence/tooling
```

The cleanup must preserve the database/Files isolation invariant established by 0031 and must not change application data, PostgreSQL schema, mutable Files bytes, retained MQTT state or normal production behaviour.

A script must not be removed merely because its name contains a feature or step number. Every candidate must first be classified from its actual callers and purpose.

## Current baseline

0031 left several feature-step tooling areas in the live source trees.

### Development / Windows

Feature-step directories include:

```text
scripts/windows/0031-step8/
scripts/windows/0031-step9/
scripts/windows/0031-step10/
scripts/windows/0031-step11/
scripts/windows/0031-step12/
scripts/windows/0031-step13/
scripts/windows/0031-step16/
```

The normal validation directory also contains a mixture of permanent behavioural protection and 0031-specific structural verification:

```text
scripts/windows/validation/verify-0031-*
```

### Production / Playbooks

The production sync source currently includes ongoing operational scripts together with 0031-specific migration/control helpers.

Expected permanent operational tooling includes:

```text
backup-db-to-binary.sh
backup-db-to-sql.sh
restore-db-from-binary.sh
restore-db-from-sql.sh
dataset-backup-manifest.py
```

Historical 0031 candidates include:

```text
step8-freeze-writes.sh
step8-capture-production-database-backup.sh
step9-reconcile-production.sh
step12-reconcile-production.sh
step12-compare-reconciliation.py
step13-capture-production-control.sh
step14-production-deployment.sh
```

`migration0024ImageCatalogue.sh` requires an explicit supported-vs-historical decision.

The Playbooks role synchronizes the `sync/` tree without unrestricted deletion, so removing a script from source does not automatically remove an already-deployed copy from `pluto`.

## Classification model

Every candidate must end in one of these states:

| Classification | Meaning | Final location |
| --- | --- | --- |
| `KEEP-OPERATIONAL` | supported normal operator/admin command | normal live script directory |
| `KEEP-REGRESSION` | permanent behaviour/safety regression protection | stable validation/test directory |
| `PROMOTE/RENAME` | still needed permanently, but feature/step naming is misleading | stable live location with behaviour-oriented name |
| `ARCHIVE` | completed-feature implementation/evidence tooling | completed feature evidence/tooling |
| `REMOVE` | redundant and already preserved sufficiently elsewhere | removed, with reason recorded |
| `PENDING` | purpose/callers not yet proven | remain untouched until resolved |

No file may move from `PENDING` directly to deletion.

## Working rules

1. Search callers before changing paths or names.
2. Preserve completed-feature evidence before removing live copies.
3. Prefer behaviour-oriented names for permanent tools and tests.
4. Do not modify historical runtime evidence merely to make old paths look current.
5. Historical documentation may describe the path that was valid at the time; update it only where it is intended to remain runnable.
6. Do not introduce global `rsync --delete` to clean production.
7. Remove stale production files only through an explicit allow-listed list.
8. Keep the ongoing 0031 database/Files pairing guards and backup/restore semantics intact.
9. Treat `migration0024ImageCatalogue.sh` as an explicit design decision, not an automatic cleanup candidate.
10. Capture before/after inventories for Windows, Playbooks source and `pluto`.
11. Each implementation step gets its own `evidence/Step N/` record and close-out decision.
12. A rollback restores only the specifically moved/renamed script or test; never restore an old script directory wholesale over newer source.

---

## Step 1 — Freeze the live tooling inventory and find every reference

**Implementation status — COMPLETE 2026-10-03:** source-side inventories, the cross-repository reference map, initial disposition and exact deployed `pluto` scripts inventory are captured under `evidence/Step 1`. The production inventory reconciles to the current deployment model with no unexplained deployed-only scripts. All seven 0031 production helpers are byte-identical to source; the only synchronized-file drift is the non-executable `README.md`, recorded in `PLUTO-RECONCILIATION.md`. No live tooling was changed by Step 1.

Before moving anything, capture the exact current contents of:

```text
scripts/windows/
scripts/windows/validation/

roles/diaries/files/sync/scripts/
roles/diaries/tests/
roles/diaries/tasks/

pluto:<production Diaries project>/scripts/
```

For every 0031 or older feature-specific candidate, search both repositories for:

```text
filename references
relative-path references
documentation references
test references
batch/PowerShell/shell callers
Gradle or npm callers
Ansible task/template references
operator runbook references
```

Include references from completed change-control records, but distinguish:

```text
historical documentation reference
```

from:

```text
active runtime/build/deployment caller
```

The latter blocks archival/removal until dealt with.

Create a working disposition table containing at least:

```text
script/test
repository
current path
deployed path, if any
active callers
historical references
current purpose
proposed classification
proposed final path
risk/notes
```

Do not move, rename or delete anything in this step.

**Evidence**

Store under:

```text
evidence/Step 1/
```

including:

```text
WINDOWS-SCRIPTS-BEFORE.txt
WINDOWS-VALIDATION-BEFORE.txt
PLAYBOOKS-SCRIPTS-BEFORE.txt
PLAYBOOKS-TESTS-BEFORE.txt
PLUTO-SCRIPTS-BEFORE.txt
REFERENCE-MAP.md
INITIAL-DISPOSITION.csv or .md
```

**Complete when**

Every cleanup candidate has known references and an initial classification, and there are no unexplained active callers.

---

## Step 2 — Approve the final tooling disposition and archive layout

**Complete — 2026-10-03.**

The final 60-row disposition is frozen in `evidence/Step 2/FINAL-DISPOSITION.csv`: 43 `ARCHIVE`, 17 `PROMOTE/RENAME`, and no pending candidates. The explicit 0024 decision is **B — completed migration tooling** for `migration0024ImageCatalogue.sh`. The archive layout is frozen in `ARCHIVE-MAP.md`, including separate 0031 Diaries/Playbooks validation areas, 0026 historical validation tooling and the 0024 production migration wrapper. The exact future production live-script removal set contains eight files and is recorded in `PRODUCTION-REMOVAL-LIST.txt`. No live file was changed by Step 2.

Review the Step 1 classification and freeze the final disposition before changing live directories.

For each candidate choose exactly one:

```text
KEEP-OPERATIONAL
KEEP-REGRESSION
PROMOTE/RENAME
ARCHIVE
REMOVE
```

Resolve especially:

### Windows `0031-step*`

Decide which, if any, still provide supported administration. The default expectation is that Step 8–16 migration/evidence harnesses become historical tooling rather than permanent operator commands.

### `verify-0031-*`

Separate:

```text
permanent behavioural assertions
```

from:

```text
checks whose only purpose is proving that retired Step N tooling exists
```

Permanent assertions may be retained or promoted to behaviour-oriented names. Historical structural tests should move with their feature tooling.

### Production `stepN-*`

Freeze the explicit list to archive/remove from:

```text
roles/diaries/files/sync/scripts/
```

and later from `pluto`.

### `migration0024ImageCatalogue.sh`

Make and record one of these decisions:

```text
A. supported permanent administration
   -> promote/rename to a feature-neutral reconciliation command

B. completed migration tooling
   -> archive and remove from live production scripts
```

If promoted, define its permanent name, interface, documentation and callers now.

Freeze the archive layout. Recommended:

```text
change-control/complete/
  0031-FEAT - isolate mutable Files storage by database environment/
    evidence/
      tooling/
        windows/
        production/
        validation/
```

Where a tool belongs more naturally to an earlier feature such as 0024, document that choice rather than duplicating it unnecessarily.

**Evidence**

```text
evidence/Step 2/DISPOSITION.md
evidence/Step 2/ARCHIVE-MAP.md
evidence/Step 2/PRODUCTION-REMOVAL-LIST.txt
```

**Complete when**

Every candidate has an approved final classification/path and `migration0024ImageCatalogue.sh` has an explicit decision.

---

## Step 3 — Preserve completed-feature tooling before live cleanup

**Implementation status — COMPLETE 2026-10-03:** all 45 Step 2 rows with an approved archive path were copied byte-identically (43 final `ARCHIVE` candidates plus two mixed `PROMOTE/RENAME` validators requiring pre-promotion historical snapshots) into their approved completed-feature evidence/tooling locations under 0031, 0026 and 0024. `evidence/Step 3/ARCHIVE-MANIFEST.csv` records original repository/path, supplied source-bundle identity, per-file SHA-256, archived path, classification and reason; `ARCHIVE-SHA256SUMS.txt` inventories the archived copies. The supplied ZIPs contain no `.git` metadata, so commit/status is recorded as unavailable rather than inferred. No live source or deployed file was moved, renamed or deleted.

Before deleting or renaming live files, copy the approved historical tooling into its final completed-feature evidence location.

For 0031, preserve the final relevant source versions of:

```text
Windows Step 8–16 tooling selected for archive
production Step 8/9/12/13/14 tooling
historical verification helpers selected for archive
```

Preserve metadata sufficient to prove what was archived:

```text
original repository
original path
source commit/status if available
SHA-256
archived path
classification
reason
```

Do not duplicate bulky runtime evidence. The archive should preserve source/tooling, while existing `evidence/Step N/runtime/...` remains where it already lives.

Update completed-feature evidence documentation only where needed to explain:

```text
this historical command has been archived here
```

Do not rewrite the historical record to pretend the archived path existed during the original feature implementation.

Generate a checksum inventory for the archived tooling.

**Evidence**

```text
evidence/Step 3/ARCHIVE-CONTENTS.md
evidence/Step 3/ARCHIVE-SHA256SUMS.txt
```

**Complete when**

Every file scheduled for archival/removal has a verified historical copy, or the disposition explicitly records why Git history alone is sufficient.

---

## Step 4 — Clean the Windows development script and validation trees

**Implementation status — COMPLETE 2026-10-03:** the Step 4 Windows cleanup/verification script ran successfully on the actual checkout. The approved archived directories/files were removed, permanent validators/helpers were promoted to behaviour-oriented names, the generated after-inventories/reference check were captured, all retained Python and Node regressions passed, the exact Windows dataset-pair guard cases passed, and the focused direct-development Files runtime/Gradle check completed successfully.

Apply the approved Windows disposition.

Expected work includes:

1. remove archived completed-feature directories such as:

   ```text
   scripts/windows/0031-step8/
   ...
   scripts/windows/0031-step16/
   ```

   unless Step 2 explicitly retained/promoted an item;

2. preserve permanent common/runtime tooling such as:

   ```text
   scripts/windows/common/
   scripts/windows/development-infrastructure/
   scripts/windows/local-docker-build/
   scripts/windows/local-published-smoke/
   ```

3. rationalise `scripts/windows/validation/verify-0031-*`:

   - keep permanent behavioural checks;
   - rename/promote them where a feature-neutral name is clearer;
   - archive structural tests which only validate retired feature tooling;
   - update all regression entry points atomically.

4. update Windows script/validation README files so the live directory documents supported commands only.

5. prove no normal start/status/backup/restore/reconciliation path still expects an archived 0031 directory.

Run the Windows/static validations relevant to:

```text
dataset-pair guard
effective dataset resolution
backup/restore manifest semantics
stable /files path
normal local mode configuration
```

Do not run destructive Image lifecycle testing merely for this cleanup.

**Evidence**

```text
evidence/Step 4/WINDOWS-SCRIPTS-AFTER.txt
evidence/Step 4/WINDOWS-VALIDATION-AFTER.txt
evidence/Step 4/REFERENCE-CHECK.txt
evidence/Step 4/VALIDATION-OUTPUT.txt
```

**Complete when**

No completed 0031 `0031-step*` operator directory remains live without an explicit permanent justification, and all retained Windows regression coverage passes.

---

## Step 5 — Clean the Playbooks source and permanent production tooling model

**Implementation status — COMPLETE 2026-10-03:** the frozen Step 2 disposition has been applied to the authoritative `/home/richard/playbooks` checkout. The role source removes the eight archived production helpers (including `migration0024ImageCatalogue.sh`), retains only supported database backup/restore/manifest commands, replaces live `verify-0031-*` tests with three behaviour-oriented regressions, updates current production documentation, and adds the exact eight-name Ansible stale-script removal allow-list without `rsync --delete`. The three permanent validators all pass with `python3` against the authoritative checkout and the Step 5-specific `git diff --check` is clean. No deployment to `pluto` was performed; that remains Step 6.

Apply the approved Playbooks-source disposition.

Expected actions:

1. remove archived 0031 helpers from:

   ```text
   roles/diaries/files/sync/scripts/
   ```

2. keep the supported ongoing database backup/restore and dataset-manifest commands;

3. implement the Step 2 decision for `migration0024ImageCatalogue.sh`:

   - rename/promote it and update callers/docs; or
   - archive/remove it;

4. rationalise:

   ```text
   roles/diaries/tests/verify-0031-*
   ```

   into permanent behavioural regression coverage vs historical structural checks;

5. update production script README/documentation;

6. add a narrowly scoped Ansible removal list for already-deployed obsolete scripts.

The removal task should conceptually be an explicit list such as:

```yaml
state: absent
loop:
  - step8-freeze-writes.sh
  - step8-capture-production-database-backup.sh
  - ...
```

The exact names must come from Step 2.

Do not add unrestricted:

```text
rsync --delete
```

to the whole production sync.

Run the Playbooks source/regression validators before deployment.

**Evidence**

```text
evidence/Step 5/PLAYBOOKS-SCRIPTS-AFTER.txt
evidence/Step 5/PLAYBOOKS-TESTS-AFTER.txt
evidence/Step 5/ANSIBLE-REMOVAL-LIST.txt
evidence/Step 5/VALIDATION-OUTPUT.txt
```

**Complete when**

The Playbooks source contains only supported live production tooling, the explicit stale-file removal is narrowly scoped, and source validations pass.

---

## Step 6 — Deploy the production cleanup non-destructively and verify `pluto`

Capture a fresh pre-deployment production inventory and compare it with the Step 1 baseline.

Deploy the Playbooks cleanup using the normal controlled Diaries deployment path.

The deployment must only affect script/tooling files and related documentation/configuration required to remove those scripts. It must not:

```text
restore a database
modify database rows
change the PostgreSQL schema
modify mutable Files contents
run Image lifecycle mutations
clear retained MQTT state
```

After deployment, capture:

```text
pluto production scripts directory
file ownership/mode for retained operational scripts
service/container status
normal Diaries status output
```

Verify explicitly:

- every approved retired helper is absent;
- every permanent operational script is still present;
- backup/restore scripts remain executable;
- the dataset-manifest helper remains present if retained;
- production responder/database/Files configuration is unchanged;
- the Diaries application is healthy.

If the role source removes a file but the deployed copy survives, treat the step as failed; that is precisely the stale-script condition this feature must eliminate.

**Evidence**

```text
evidence/Step 6/PLUTO-SCRIPTS-PRE.txt
evidence/Step 6/PLAYBOOK-OUTPUT.txt
evidence/Step 6/PLUTO-SCRIPTS-POST.txt
evidence/Step 6/PRODUCTION-STATUS.txt
evidence/Step 6/DIFF.md
```

**Rollback**

Restore only the specifically required script from its archived/source version and reclassify it. Do not restore the entire old `scripts` directory wholesale.

**Complete when**

`pluto` contains no approved retired helpers, supported operational tooling remains intact, and production health/status checks pass.

**Complete — 2026-10-03.** A fresh pre-deployment `pluto` capture matched the Step 1 production baseline. The guarded `mango` deployment reran all three permanent Playbooks validators, then deployed through the normal Diaries `--tags copy` path. Ansible removed exactly the eight allow-listed obsolete helpers and finished with `failed=0`, `unreachable=0`, exit code `0`. Post-deployment verification proves the supported production script set remains intact, retained operational helpers match the approved Step 5 hashes and executable modes, `.env`, `compose.yaml` and responder configuration fingerprints plus non-secret database/Files selectors are unchanged, and all five required Diaries services are running and healthy. `DIFF.md` and `VERIFICATION-OUTPUT.txt` record the final PASS.

---

## Step 7 — Add permanent anti-accumulation guards and feature-close-out guidance

**Complete — 2026-10-03; managed-production-scripts refinement added the same day.** The permanent Windows `verify-live-script-policy.py` guard enforces the supported live top-level areas and rejects unclassified feature/step-shaped tooling with an explicit exact-path exception mechanism; `verify-dataset-pair-guard.py` runs it through the normal local safety-regression path. The production deployment-contract regression enforces the exact supported static script set, feature/step-name policy and the dedicated managed-script deployment boundary. Production `scripts/` is synchronized separately with `--delete` and `--delete-excluded`; the wider project sync excludes `scripts/`, and permanent templated scripts are explicitly protected then rendered normally. This removes the need for an ever-growing one-off stale-script removal list while keeping destructive synchronization narrowly scoped. Change-control, Windows operator/validation and Playbooks production documentation require feature-close-out classification/archive/removal and explicit deploy/remove handling for temporary production helpers. `evidence/Step 7/GUARD-TESTS.txt` records the targeted PASS results; this refinement itself performs no production deployment or data mutation.

Prevent 0032 from becoming a one-time cleanup.

Add a permanent source guard which detects completed-feature tooling appearing in live script trees without an explicit supported classification.

At minimum consider patterns equivalent to:

```text
scripts/windows/NNNN-step*/
roles/diaries/files/sync/scripts/stepN-*
```

The guard must be policy-aware rather than a naïve filename ban. It should permit explicitly approved permanent tools and avoid rejecting unrelated legitimate names.

Prefer checking:

```text
live operational directories
against
an explicit small allow-list / naming policy
```

rather than encoding a list of every historical feature forever.

Add the guard to the normal relevant regression entry point.

Update change-control guidance/template documentation with the permanent close-out rule:

> Classify every script introduced by the feature as permanent operational tooling, permanent regression tooling, or historical feature tooling. Archive/remove historical tooling from live script directories and, where applicable, verify that deployed copies have also been removed.

Also document the production rule:

```text
temporary feature-only production helper
    must be explicitly deployed
    and explicitly removed during feature close-out
```

rather than being placed indefinitely in the always-synchronized production tree.

**Evidence**

```text
evidence/Step 7/GUARD-TESTS.txt
evidence/Step 7/DOCUMENTATION-CHANGES.md
```

**Complete when**

A regression check would catch the same accumulation pattern that caused 0032, and future feature close-out guidance explicitly requires script classification/removal.

---

## Step 8 — Run final regression, compare before/after inventories and close 0032

**Implementation status — COMPLETE 2026-10-03:** final source/deployment inventories and the 60-row disposition are reconciled under `evidence/Step 8`. The Windows host gate passes permanent source/storage/backup checks, all 11 Node tests, responder/web Gradle tests and the Angular production build. The `mango` host gate passes all three permanent Playbooks validators plus native `ansible-playbook --syntax-check diaries.yaml`. All 11 acceptance criteria PASS, Step 6 remains the authoritative verified `pluto` after-state, and 0032 is closed under `change-control/complete/`.

Run the full relevant final regression against the exact cleanup candidate.

At minimum include:

### Diaries

```text
permanent storage-isolation/path guards
backup/restore safety checks
Windows script/reference checks
responder/web Java tests
Angular production build where used by the normal final gate
```

### Playbooks

```text
Diaries role source validators
production storage-isolation guards
backup/restore semantics
Ansible syntax/source validation
new stale-tooling guard
```

Do not recreate archived Step N tooling merely so old structural tests can pass. A test which requires retired tooling should itself have been reclassified in Steps 4 or 5.

Create final before/after comparison tables for:

```text
Windows live scripts
Windows permanent validation
Playbooks live production scripts
Playbooks permanent tests
pluto deployed scripts
```

Create a final disposition table with one row per original candidate:

```text
original path
classification
final live/archive path
renamed?
production removed?
evidence
```

Review every 0032 acceptance criterion and leave no unexplained pending row.

Move 0032 from:

```text
change-control/todo/
```

or its implementation-time `in-progress` location to:

```text
change-control/complete/
```

only after the final regression and production verification pass.

**Evidence**

```text
evidence/Step 8/FINAL-DISPOSITION.md
evidence/Step 8/BEFORE-AFTER.md
evidence/Step 8/FINAL-REGRESSION.txt
evidence/Step 8/ACCEPTANCE-MATRIX.md
evidence/Step 8/CLOSE-OUT.md
```

**Complete when**

All 0032 acceptance criteria are evidenced, live script directories contain only supported tooling, `pluto` contains no stale retired feature helpers, permanent regression coverage still passes, and the recurrence guard is active.

---

## Expected implementation sequence

The intended order is:

```text
Step 1  inventory + references
   |
Step 2  approve classification/disposition
   |
Step 3  preserve/archive historical tooling
   |
Step 4  clean Windows source/tests
   |
Step 5  clean Playbooks source/tests + prepare explicit deployed removal
   |
Step 6  deploy cleanup to pluto and verify
   |
Step 7  add permanent recurrence guards/guidance
   |
Step 8  full regression + close-out
```

Steps 1–3 are deliberately conservative. No live cleanup should begin before the archive and disposition are frozen.

## Acceptance mapping

The feature-level acceptance criteria should be proven primarily by these steps:

| Acceptance concern | Primary step |
| --- | --- |
| No completed 0031 Windows step directories remain live | Step 4 |
| No retired 0031 production step scripts remain in Playbooks source | Step 5 |
| No stale retired scripts remain on `pluto` | Step 6 |
| Supported operational commands remain present | Steps 4–6 |
| Removed scripts are preserved or explicitly justified | Steps 2–3 |
| Permanent tests protect behaviour rather than retired feature structure | Steps 4–5 |
| `migration0024ImageCatalogue.sh` has explicit disposition | Steps 2 and 5 |
| No application/database/Files/MQTT data mutation from cleanup | Steps 3–8 |
| Relevant Diaries/Playbooks regression passes | Step 8 |
| Recurrence is detectable/prevented | Step 7 |
| Exact before/after inventory is recorded | Steps 1, 6 and 8 |

## Final close-out rule

0032 is not complete merely because the source directories look tidier.

It is complete only when:

1. every original candidate has a recorded disposition;
2. historical tooling has been preserved where required;
3. live Windows and production source trees contain only supported tooling;
4. deployed stale production copies have actually been removed from `pluto`;
5. permanent behavioural regressions still pass;
6. the `migration0024ImageCatalogue.sh` decision is implemented and documented;
7. the anti-accumulation guard is active;
8. before/after inventories and the final acceptance matrix are complete.
