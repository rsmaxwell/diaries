# 0034-FEAT Step 8 — `mango` regression evidence (2026-10-09)

**Origin:** User-supplied `mango` terminal captures `note(20261009-145053).txt`, `note(20261009-145137).txt` and `note(20261009-145246).txt`. This file is an accurately transcribed **outcome summary**, not a claim to reproduce the complete terminal transcripts verbatim.

## Full source suite, from `richard@mango:~/playbooks`

| # | Executed command | Observed outcome |
|---|---|---|
| 1 | `python3 roles/diaries/tests/verify-complete-dataset-manifest.py` | PASS — complete-dataset directory and manifest contract verified |
| 2 | `python3 roles/diaries/tests/verify-complete-dataset-publisher.py` | PASS — isolated publisher suite |
| 3 | `python3 roles/diaries/tests/verify-complete-dataset-replication.py` | PASS — isolated replication suite |
| 4 | `python3 roles/diaries/tests/verify-production-backup-restore-semantics.py` | PASS — database-only backup/restore and dataset contract frozen |
| 5 | `python3 roles/diaries/tests/verify-production-btrfs-strategy.py` | PASS — historical Step 3 legacy-capture strategy regression |
| 6 | `python3 roles/diaries/tests/verify-production-complete-dataset-tooling.py` | PASS — Step 8 complete-dataset tooling contract |
| 7 | `python3 roles/diaries/tests/verify-production-publication-contract.py` | PASS — stable publication configuration contract |
| 8 | `python3 roles/diaries/tests/verify-production-restore-source-compatibility.py` | PASS — Step 7 legacy/fixed/snapshot restore compatibility contract |
| 9 | `python3 roles/diaries/tests/verify-production-storage-isolation.py` | PASS — storage-isolation contract |
| 10 | `python3 roles/diaries/tests/verify-production-deployment-contract.py` | PASS — production deployment contract |
| 11 | `python3 roles/local-backup/tests/verify-diaries-pull.py` | PASS — Step 8 permanent `mars` pull source contract |

The transcript includes successful non-destructive restore preflights for legacy `<backup-id>`, fixed `diaries-backup` and explicit snapshot-style sources. Its negative cases reject overlapping roots, dataset mismatches, unsupported storage modes and partial/non-restorable workspaces. Tests verify that the pull helper installs disabled by default, is normal-user owned, is unscheduled and limits rsync deletion to an incoming private tree.

## Python compilation

The final capture from `richard@mango:~/playbooks` shows this command returning to the shell prompt with **no diagnostic output**:

```bash
python3 -m py_compile \
  roles/diaries/files/sync/scripts/production-complete-dataset.py \
  roles/diaries/tests/verify-production-publication-contract.py \
  roles/local-backup/files/backup-machine/diaries-pull.py \
  roles/local-backup/tests/verify-diaries-pull.py
```

**Outcome:** PASS (no syntax errors reported).

## Non-regression command observation

A separate capture shows the *production runtime* `production-complete-dataset.py` invoked with other Python file paths as arguments, producing `ERROR: required production runtime/tooling file is missing: /home/richard/playbooks/roles/diaries/files/sync/compose.yaml`. That invocation is not one of the eleven source regression commands and is not a Python syntax test; it requires a deployed runtime context. It does not invalidate the passing source suites or clean compilation. This is **not** evidence that the production runtime has been deployed or exercised by Step 8.

**Scope:** Source-only acceptance on `mango`. Production path migration, deployment, publication and live runtime verification remain Step 9 gates.
