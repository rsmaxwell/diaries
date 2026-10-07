# Step 10 production backup acceptance

Step 10 does not require another production backup because the final Step-8 operation is already the production rollout and non-destructive complete backup called for by Step 10.

## Accepted evidence

`Step 8/RUNTIME-PRODUCTION-PREFLIGHT-FINAL.txt` proves the non-destructive preflight resolved the intended production database/Files pair, running responder, NAS volume and benign staging state without stopping the writer or creating media.

`Step 8/RUNTIME-PRODUCTION-BACKUP-FINAL.txt` proves backup `20261007-145013Z`:

```text
kept PostgreSQL available
stopped diaries-responder for the coherent capture window
created database/diaries.dump
created database/diaries.sql
validated the custom dump structure
validated the SQL dump as readable plain PostgreSQL output
captured 89 durable Files / 100032776 bytes
excluded transient .image-staging
reread source Files and proved exact path/size/SHA-256 equality
wrote verification inventories/checksums
validated schema-2 media as a partial candidate
atomically promoted the candidate
validated schema-2 media again as a completed backup
restored the prior responder-running state
```

`Step 8/RUNTIME-PRODUCTION-HEALTH-FINAL.txt` proves `diaries-responder` returned to `healthy` after the backup.

The first Step-8 production attempt is also retained because it proves fail-closed behaviour: a host snapshot ownership problem prevented verification, the candidate stayed `.partial`, and the responder stayed stopped until the permanent correction was deployed.

## Restore proof boundary

No destructive production restore is performed for close-out. The destructive complete-restore proof is the accepted Step-9 disposable rehearsal `runtime-20261007-182222Z`, including safety backup, exact Files replacement, failed-postflight stopped state, rollback availability, final database/Files fingerprint equality, retained replay and representative `/files` verification.
