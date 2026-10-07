# 0033-FEAT Step 8 evidence — production complete-dataset tooling through Playbooks

## Status

**Complete — 2026-10-07. Production deployment and a real complete-dataset backup are proven.**

Step 8 source implementation now provides permanent Linux/production equivalents of the local complete-dataset tooling through the Diaries Ansible role. The role deploys the commands but does not invoke a complete restore during routine rollout.

Step 8 now has the required real production evidence: corrected Playbooks regressions, corrected Ansible check/apply output, deployed production configuration validation, non-destructive preflight, fail-closed first-backup evidence, successful corrected complete backup, and post-backup responder health. A destructive production restore was deliberately not performed; Step 9 remains the destructive restore rehearsal boundary.

## Permanent production commands

The managed production `scripts/` directory now includes:

```text
backup-dataset.sh
restore-dataset.sh
production-complete-dataset.py
complete-dataset-manifest.py
complete-dataset-verification.py
complete-dataset-restore-stage.py
complete-dataset-postflight.py
```

The existing database-only commands remain present and unchanged:

```text
backup-db-to-binary.sh
backup-db-to-sql.sh
restore-db-from-binary.sh
restore-db-from-sql.sh
dataset-backup-manifest.py
```

`restore-dataset.sh` exposes the same safety phases as local tooling:

```text
preflight
prepare   # exact RESTORE confirmation
apply     # exact APPLY confirmation
rollback
postflight
```

## Production storage/data-plane design

Production identity is derived from the deployed `.env`, including the explicit `DIARIES_FILES_DIR` rendered from inventory `diaries_files_dir`. The current invariant remains:

```text
production PostgreSQL dataset <-> production mutable Files selector/root
```

The mutable Files tree is not assumed to have a second host-level NAS mount. The orchestrator inspects the deployed responder container to discover the actual Docker volume mounted at `/data/files`, then performs copy/rename operations through a short-lived maintenance container using the already-present PostgreSQL Alpine image. This keeps the tool aligned with the exact CIFS volume used by Compose.

Complete media and restore state are kept outside the live mutable Files tree:

```text
{{ diaries_project_dir }}/data/dataset-backups/production
{{ diaries_project_dir }}/data/dataset-restores/production
```

The role creates both directories idempotently.

## Backup semantics

`backup-dataset.sh`:

1. validates deployed Compose and the `.env` identity;
2. requires PostgreSQL to remain running/ready;
3. inspects `.image-staging` and permits only absent/empty or the expected zero-byte `catalogue.lock` state;
4. records whether `diaries-responder` was running, then quiesces it if necessary;
5. captures both `database/diaries.dump` and `database/diaries.sql`;
6. captures durable Files bytes excluding `.image-staging`;
7. independently rereads the quiesced live Files tree and compares exact paths/sizes/SHA-256 through the shared verification helper;
8. writes/validates the shared schema-2 manifest in `.<backup-id>.partial`;
9. atomically promotes the local backup directory only after verification;
10. restores the prior responder-running state only after completed-media validation succeeds.

A failed capture/finalisation leaves incomplete media non-restorable and leaves the responder stopped for review.

## Restore semantics

`restore-dataset.sh preflight` is read-only. `prepare` requires `RESTORE`, records the previous responder state, quiesces the responder, creates a mandatory verified complete-dataset safety backup, and stages the selected backup's Files as a sibling of the live Files tree on the same NAS Docker volume. The staged tree is copied back to a temporary local verification mirror and independently rehashed against the backup inventory before preparation is accepted.

`apply` requires `APPLY`, restores only `database/diaries.dump`, retains the SQL dump as the companion representation, moves the current live Files root to an explicit rollback sibling, promotes the verified staged sibling by same-volume rename, creates only fresh empty runtime `.image-staging`, verifies the new live tree, and leaves the responder stopped.

`rollback` restores PostgreSQL from the mandatory complete safety backup and reinstates the retained pre-restore Files tree. `postflight` verifies database/Image counts, exact Files inventory, Image catalogue/Files reconciliation, responder health and retained replay, representative retained MARQUEE + IMAGE objects, and representative `/files` bytes before restoring the previous responder-running state and closing automatic rollback.

## Schema/inventory compatibility

The production role carries byte-identical copies of the local 0033 helpers for schema/inventory semantics. The permanent regression freezes these SHA-256 values:

```text
complete-dataset-manifest.py       6878a61aeaf4abfe561d9be2c883bb12fb2d67b72b5b7ec0b9420c018fad6cc3
complete-dataset-verification.py   b278b72383f3bae5c6ec95e2b17cc0ce12d2f3377b4f781626880484d426400a
complete-dataset-restore-stage.py  c6e9272191363c06e988d1ea849bdb57e44ac3408e74d65895aa2f9c2828cfc7
complete-dataset-postflight.py     7e04b08b033f2f98a70832248c3e60d0ea11bc03b7121852d482b396fe8ec95b
```

## Permanent regression result

The captured output is [`PLAYBOOKS-TEST-RESULTS.txt`](PLAYBOOKS-TEST-RESULTS.txt). The following permanent tests all pass together:

```text
roles/diaries/tests/verify-production-complete-dataset-tooling.py
roles/diaries/tests/verify-production-deployment-contract.py
roles/diaries/tests/verify-complete-dataset-manifest.py
roles/diaries/tests/verify-production-backup-restore-semantics.py
roles/diaries/tests/verify-production-storage-isolation.py
```

The new regression additionally proves that:

- complete-dataset commands/helpers are part of the supported managed script allow-list and have executable source permissions;
- the shared schema/inventory helpers match the frozen local versions;
- the production engine derives Files identity from the deployed explicit selector;
- responder quiescence does not stop PostgreSQL;
- complete artifacts/state stay outside the mutable NAS Files root;
- restore stages/verifies replacement Files and retains executable rollback semantics;
- apply restores only the custom dump and does not apply the SQL companion afterwards;
- existing database-only commands remain explicitly database-only;
- routine Ansible tasks deploy the new commands but never invoke backup or restore automatically.


## Real production rollout evidence — 2026-10-07

The final production rollout evidence is retained verbatim alongside this README:

```text
RUNTIME-ANSIBLE-CHECK-FINAL.txt
PLAYBOOKS-TEST-RESULTS-CORRECTED.txt
RUNTIME-ANSIBLE-DEPLOY-FINAL.txt
RUNTIME-PRODUCTION-PREFLIGHT-FINAL.txt
RUNTIME-PRODUCTION-BACKUP-FIRST-ATTEMPT.txt
RUNTIME-PRODUCTION-BACKUP-FINAL.txt
RUNTIME-PRODUCTION-HEALTH-FINAL.txt
```

### Corrected regression and Ansible deployment

After the initial dry run revealed transient `__pycache__` / `*.pyc` files would be synchronized, the managed-script rsync was permanently corrected to exclude interpreter caches under the existing `--delete-excluded` policy. The corrected Playbooks regression proves both cache exclusion and the production complete-dataset contract, including the later host-snapshot ownership fix.

The final Ansible `--check --diff` run planned only the intended complete-dataset scripts and no Python cache artifacts, while the real `--tags copy` deployment completed with `failed=0`. Rendered production validation for `DIARIES_FILES_DIR`, `/data/files`, the shared diary scan mount and broker flow-control policy all passed.

### Production preflight

The final non-destructive production preflight resolved:

```text
Logical dataset:    production
Database identity:  docker-volume:diaries-db-data / diaries
Files selector:     files
Docker NAS volume:  diaries_nas-photo
Responder running:  True
Staging:            excluded-benign (1 entries)
```

and explicitly confirmed that no writer was stopped and no backup workspace was created.

### First real backup — fail closed

[`RUNTIME-PRODUCTION-BACKUP-FIRST-ATTEMPT.txt`](RUNTIME-PRODUCTION-BACKUP-FIRST-ATTEMPT.txt) proves the intended failure-state semantics. PostgreSQL capture and structural dump validation succeeded, but the root maintenance-container tar extraction propagated restrictive NAS/root metadata onto the host backup `files/` directory. Host-side verification therefore could not traverse the snapshot. The candidate remained under `.<backup-id>.partial`, was never promoted, and the responder was deliberately left stopped for review.

The permanent correction:

- returns root-written host snapshots/verification mirrors to the invoking operator UID/GID;
- defensively removes and asserts absence of transient `.image-staging` from host backup media;
- makes all tar data-plane pipelines propagate source/extraction failures;
- is protected by the permanent production complete-dataset regression.

### Successful corrected production backup

After the correction was deployed, [`RUNTIME-PRODUCTION-BACKUP-FINAL.txt`](RUNTIME-PRODUCTION-BACKUP-FINAL.txt) proves successful complete production media creation:

```text
Backup ID:          20261007-145013Z
Logical dataset:    production
Database dumps:     database/diaries.dump + database/diaries.sql
Durable Files:      89 files / 100032776 bytes
Source match:       exact paths/sizes/SHA-256
SQL dump:           readable PostgreSQL plain dump
Manifest:           schema-2; valid as partial candidate and completed backup
Final backup:       data/dataset-backups/production/20261007-145013Z
Prior writer state: restored
```

The responder was stopped only for the capture/finalisation window and then restored to its prior running state. [`RUNTIME-PRODUCTION-HEALTH-FINAL.txt`](RUNTIME-PRODUCTION-HEALTH-FINAL.txt) subsequently shows `diaries-responder` running `rsmaxwell/diaries-responder:0.0.9-build-84` and reporting `healthy`.

No destructive production restore was performed merely to close Step 8. Restore correctness remains proven by the local implementation/regressions and is exercised destructively in the disposable Step 9 rehearsal before final production rollout/feature close-out.

## Completion boundary

**Step 8 is complete.** Production now has the same supported schema-2 complete-backup format and phased restore semantics as the local tooling, deployed through the normal Playbooks path without weakening the existing database-only commands. The complete production backup path has been demonstrated with real data and restored application health.

The evidence establishes all Step 8 completion criteria:

- permanent production scripts/helpers are deployed and executable;
- explicit production database/Files identity is preserved;
- existing database-only commands remain unchanged and explicitly database-only;
- Ansible check/apply is clean and managed-script hygiene excludes transient Python caches;
- production preflight is non-mutating and resolves the intended dataset;
- failed backup media remains non-restorable and leaves the responder stopped;
- corrected complete backup media contains both database formats plus the exact durable Files snapshot;
- schema-2 verification succeeds before and after atomic promotion;
- prior responder state is restored only after completed-media validation;
- final responder health is green.

A destructive production restore is not a Step 8 completion requirement and was not performed.
