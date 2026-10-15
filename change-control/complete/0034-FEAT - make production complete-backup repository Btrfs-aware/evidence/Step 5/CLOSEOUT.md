# 0034-FEAT — Step 5 formal close-out

**Status: CLOSED — isolated publisher implementation and source regressions**  
**Close-out date:** 2026-10-09  
**Scope:** Isolated publisher only; not deployed or enabled on production.

## Implemented

- `roles/diaries/files/sync/scripts/complete-dataset-publisher.py` publishes already-complete schema-2 generations under the stable `diaries-backup` path.
- Staging verification precedes publication; publication uses atomic symlink replacement, shared/exclusive locking, and preserves the previous valid generation.
- `roles/diaries/tests/verify-complete-dataset-publisher.py` covers synthetic schema-2 input, non-mutating preflight, successful publications, corrupt candidate refusal, duplicate ID refusal, concurrent reader locking and temporary artefact cleanup.

## Evidence and regression disposition

- Operator `mango` log `RUNTIME-MANGO-REGRESSIONS-20261009.txt` shows the 14 dedicated publisher checks **PASS**.
- Operator log also shows the manifest, backup/restore, complete tooling, and storage-isolation regressions **PASS**.
- The deployment-contract regression initially reported `FAIL: role source contains only the approved supported production script set`, after the Step 5 publisher was added. This is a maintenance allowlist omission, not evidence of a clean five-suite run.
- Corrected `roles/diaries/tests/verify-production-deployment-contract.py` to classify the new permanent `complete-dataset-publisher.py` in `SUPPORTED_SCRIPTS`; re-ran the deployment-contract suite against the recovered Playbooks bundle with **PASS**. See `SOURCE-REGRESSION-DEPLOYMENT-CONTRACT.txt`.
- The corrected regression should be rerun on `mango` after applying the Playbooks overlay; this close-out records source verification and the original operator evidence separately.

## Boundaries and deferred work

The isolated publisher is **not wired into** `backup-dataset.sh`, live database/NAS capture, deployed Ansible role configuration, `pluto` rsync, or receiving-side Btrfs snapshots. It must not be treated as enabled production behaviour. Steps 6 onward implement safe replication and integration. Existing 0033 complete backups and schema-2 format remain unchanged.

**Disposition:** Step 5 isolated scope accepted and closed; 0034-FEAT remains in progress. Proceed to Step 6 (replication-safe read contract).
