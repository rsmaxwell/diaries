# 0033-FEAT Step 10 evidence — production rollout, operating documentation and close-out

## Status

**COMPLETE — 2026-10-07**

Step 10 closes 0033 without performing a redundant second production capture. The production deployment and non-destructive complete backup required by this step were already completed and retained as Step-8 evidence while implementing/proving the permanent production path.

The accepted production backup is:

```text
backup id:          20261007-145013Z
logical dataset:    production
database identity:  docker-volume:diaries-db-data / diaries
Files selector:     files
Docker NAS volume:  diaries_nas-photo
Files inventory:    89 durable files / 100032776 bytes
manifest:           schema 2, completed and independently validated
writer state:       prior running responder restored
post-backup state:  diaries-responder healthy
```

See `../Step 8/RUNTIME-PRODUCTION-PREFLIGHT-FINAL.txt`, `../Step 8/RUNTIME-PRODUCTION-BACKUP-FINAL.txt` and `../Step 8/RUNTIME-PRODUCTION-HEALTH-FINAL.txt` for the verbatim production output. The backup finalisation itself reread the quiesced source Files tree and proved exact path/size/SHA-256 equality, so the production evidence contains both media verification and source-read verification. A destructive production restore is deliberately not repeated: the accepted Step-9 disposable rehearsal is the restore proof.

## Step-10 changes

Normal operating documentation is updated in:

```text
README.md
scripts/windows/README.md
Playbooks roles/diaries/README.md
Playbooks roles/diaries/files/sync/scripts/README.md
```

The documentation now makes explicit:

- when database-only backup is appropriate;
- when complete-dataset backup is the required recovery unit;
- schema-2 directory layout and `.partial` promotion semantics;
- effective database + Files identity selection;
- writer-quiescence/downtime and fail-stopped behaviour;
- the independent completed-media verification command;
- phased complete restore (`preflight`, `prepare`, `apply`, `postflight`, `rollback`);
- mandatory verified pre-restore safety backup;
- exact/replacement Files semantics rather than merge;
- `.image-staging` policy;
- what complete-dataset media deliberately excludes.

`SCRIPT-INVENTORY.md` records the final 0033 tool classification. There is no Step-9 rehearsal helper in the live Windows or production operator script set; the disposable rehearsal harness remains under `evidence/Step 9/tooling/` only.

## Closure decision

All acceptance criteria in the feature README are satisfied. 0031's one-database/one-Files-root invariant remains unchanged, the database-only commands remain explicitly database-only, and 0032's managed/live-script hygiene remains in force.

0033 is therefore complete and its complete change-control directory is moved from `in-progress` to `complete`.
