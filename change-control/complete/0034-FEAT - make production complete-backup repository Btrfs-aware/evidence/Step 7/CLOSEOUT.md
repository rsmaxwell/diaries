# 0034-FEAT — Step 7 formal close-out

**Step:** 7 — Preserve historical restore and compatibility  
**Status:** **CLOSED**  
**Date:** 2026-10-09  
**Scope:** Production schema-2 restore-source compatibility, not a new backup format or a production restore.

## Implemented contract

- Existing `<backup-id>/` historical source remains selectable.
- `diaries-backup` / `diaries-backup/` select the stable published schema-2 source.
- Explicit completed-directory paths are accepted for future read-only 0035 snapshot-history handoff.
- Continuation after prepare remains pinned to the exact source, including after the fixed publication advances or a same-ID historical backup exists.
- Dataset mismatch, partial workspace, manifest/inventory validation and exact `RESTORE` confirmation guards remain enforced.
- `diaries-backup-history` ownership and live snapshot integration remain with 0035; history lookup never performs restore.

## Acceptance evidence

### 1. `mango` source regression — PASS

**Operator transcript:** `note(20261009-141643).txt`.

All six suites returned PASS:

```text
python3 roles/diaries/tests/verify-production-restore-source-compatibility.py
python3 roles/diaries/tests/verify-complete-dataset-manifest.py
python3 roles/diaries/tests/verify-production-backup-restore-semantics.py
python3 roles/diaries/tests/verify-production-complete-dataset-tooling.py
python3 roles/diaries/tests/verify-production-storage-isolation.py
python3 roles/diaries/tests/verify-production-deployment-contract.py
```

The new disposable compatibility suite expressly passed historical ID, fixed selector, explicit snapshot-style directory, dataset mismatch rejection, negative `RESTORE` confirmation without writer stop/mutation, same-ID source precedence, prepared-source pinning after publication advances, and partial-workspace refusal.

### 2. `pluto` deployment — PASS

**Operator transcript:** `note(20261009-141957).txt`.

Normal Playbooks `./scripts/diaries.sh` deployment completed:

```text
pluto : ok=46 changed=2 unreachable=0 failed=0 skipped=12
```

Managed production scripts were synchronized and the Compose-stack handler ran. No Ansible failures or unreachable hosts.

### 3. Deployed source inventory — PASS

**Operator transcript:** `note(20261009-142144).txt`.

- Historical completed backup: `20261007-145013Z/`.
- Fixed pointer: `diaries-backup -> .diaries-backup-generations/20261007-145013Z`.
- Existing `.20261007-143438Z.partial/` remains present and is not accepted as a completed restore source.
- Deployed help supports `<backup-id|diaries-backup|directory>` selectors.

### 4. `pluto` live non-destructive preflights — PASS

**Operator transcripts:** `note(20261009-142307).txt`, `note(20261009-142342).txt`, `note(20261009-142410).txt`.

| Source selector | Result | Resolved source |
| --- | --- | --- |
| `20261007-145013Z` | `PREFLIGHT OK` | `.../production/20261007-145013Z` |
| `diaries-backup` | `PREFLIGHT OK` | Fixed published generation for backup ID `20261007-145013Z` |
| `data/dataset-backups/production/.diaries-backup-generations/20261007-145013Z` | `PREFLIGHT OK` | Explicit generation directory |

All three independently reported:

- `Schema: 2`, `Logical dataset: production`, `Workspace: completed backup`.
- `Files in backup: 89 / 100032776 bytes`.
- PostgreSQL custom dump structurally readable; database target `docker-volume:diaries-db-data / diaries`.
- `Responder running: True`, `Target staging: excluded-benign (1 entries)`.
- `PREFLIGHT OK: no writer was stopped, no safety backup was created, and no Files staging directory was created.`

### Evidence limits / deferred work

- The original suggested **live** `printf 'NO\n' | ./restore-dataset.sh prepare diaries-backup` and `./status.sh` commands were **not supplied**; do not claim they ran. The same refusal logic and lack of mutation were tested in disposable source regression; live preflight independently established the responder was running.
- The third live selector was an **explicit generation directory**, not an actual read-only Btrfs snapshot. Real 0035 `diaries-backup-history path` handoff and snapshot restore rehearsal remain later cross-feature acceptance gates.
- No production `prepare`, `apply`, `rollback`, destructive restore, or restore-data comparison was run; none is asserted here.
- No Java/Angular code changed and no new Docker images were required.

## Closure decision

**Step 7 is formally CLOSED (2026-10-09).** Legacy, fixed-publication and explicit-directory schema-2 restore preflight compatibility is implemented, regressions are green, deployment succeeded and non-destructive production verification passed. Remaining cross-feature 0035 and actual end-to-end restore rehearsals stay open in their respective later steps; closure here does not waive those gates.
