# 0029-FEAT — Step 3 production-shaped isolated migration rehearsal

**Status:** PREPARED, NOT EXECUTED. This is a release-preparation test, not production deployment approval.

## Source evidence

- 26 November 2026 12:43 GMT production read-only gate: `GATE=PASS`; 11 Page-less Fragments exactly `{1,2,3,387,806,1177,1563,1564,1738,1926,2061}`, 2,331 Fragments, 2,270 Marquees, zero bad owners, destination Pages 1005 and 1078 present, `fragment.placement` absent, `marquee.page_id` present.
- Development: all six Editor/Reader browser acceptance checks passed; full responder regression passed; 2,269 Marquees migrated; MQTT synchronisation of 10,661 retained topics passed.
- Corrected production MQTT ACL exists in the Playbooks checkout, but was not yet deployed as of this report.

## Execution

Terminal: Windows 11 — Cygwin Bash, from Diaries parent repo root:

```bash
cd /cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries
bash 'change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling/tools/run-step3-isolated-production-migration-rehearsal.sh'
```

Prerequisites: local Docker engine and `postgres:18-alpine` image; SSH access to `pluto`; running `diaries-postgres` there; five existing SQL files in the feature's `tools/`. The script uses **SSH `docker exec pg_dump` only** on production, streams data to a **local `--network none` PostgreSQL container**, runs all SQL there, and removes the container on exit. A failed source dump must fail the pipeline. All logs stay in this feature under `evidence/step-3-production-isolated-rehearsal/`.

The script tests: exact production baseline, 11-row hybrid conversion, nine PREAMBLEs plus two exceptional dated assignments, Marquee column drop, reverse-order rollback of both stages, exact recovery of the original baseline, and forward reapplication. Both Fragment and Marquee row counts must remain unchanged.

**Not covered:** testing the restorable *scheduled* production database backups, restoring the mutable Files dataset, packaging/publishing immutable application images, verifying effective Ansible deployment variables, or verifying MQTT reconciliation after actual production startup. Those remain separate release gates. The streamed pg_dump is an isolated test input, **not** the approved production recovery backup.

## Production rollout constraints

- Production currently uses Client `0.0.9-build-80`, Responder `0.0.9-build-86`, Reader `0.0.9-build-9` (26 November 2026 baseline).
- Commit compatible Client/Responder/Reader changes separately in their submodules, then update the parent Git pins. Preserve unrelated local work. Verify actual build provenance before publishing images.
- Production backup must be separately verified and restorable, with complete Files recovery coverage and recorded immutable checksums/locations; do not overwrite or delete backup datasets.
- Coordinate application writer shutdown, PostgreSQL migrations, MQTT ACL update and compatible image deployment. Do not start the old responder against the migrated schema. Maintain a tested rollback plan and a clear stop/go gate for operator approval.
- Do not claim Step 3 production CLOSED based solely on this isolated rehearsal.
