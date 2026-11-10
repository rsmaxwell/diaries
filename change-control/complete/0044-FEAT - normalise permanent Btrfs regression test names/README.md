# 0044-FEAT — Normalise permanent Btrfs replication regressions

**State:** CLOSED — accepted 10 November 2026; published Playbooks source and final regression evidence verified.

## Purpose and scope

Retain only meaningful permanent regression coverage for the current Btrfs replication implementation. Remove feature-numbered and transitional `simplified` filenames; retire migration-only tests after preserving their historical copies. Changes are confined to Playbooks regression source, READMEs, and Diaries change-control evidence. There is no deployment, snapshot operation, restore, replication, or changes to running configuration.

## Final permanent regression suite

Under `/home/richard/playbooks/roles/btrfs-replication/tests/`:

- `README.md` — current regression execution guidance.
- `verify-replication.py` — protocol, state validation and recovery handling (25 unit tests PASS on 10 Nov).
- `verify-protection.py` — agreed-parent protection and current pruning planners (5 unit tests PASS).
- `verify-shared-retention.py` — policy and retention guards (PASS).

Both obsolete `verify-legacy-retirement-source.py` and `verify-simplified-cutover-readiness.py` were retired. Their historical source copies are retained in this feature's `tests/` directory and original regression outcomes in `evidence/`. The permanent agreed-parent three-planner protection assertion was retained in `verify-protection.py` before the cutover-specific test was removed.

## Implementation receipts — Playbooks repository on `mango`

| Action | Commit (main) | Acceptance |
|---|---|---|
| Remove `0040` prefixes from five scripts and correct README references | `06cf0886a863ce2d4d5e19289fc1fbf124d97554` | Five regression entry points PASS; no script content changes |
| Consolidate redundant legacy-retirement test | `b393602f3086a570e429dbec57d1a9ff1db7304b` | 25 replication, 4 protection and 6 cutover tests PASS; retention PASS |
| Retire cutover-readiness test while retaining ongoing pin guard | `4c17fac7455d8fa8a3f4caa1dd003eaac2427c32` | 25 replication, 5 protection; retention PASS |
| Remove `simplified` from permanent names, rename README | `7dfa93fef6d975aa82f5f4cfdf54497b106e7645` | 25 replication, 5 protection; retention PASS; staged diff validated; clean tree |

Latest readback: Playbooks `main` was **four commits ahead of `origin/main`**, with a clean working tree; publication remains to be verified.

## Evidence and historical material

- `reports/RENAME-ACCEPTANCE-20261110.md` and `evidence/Step 1/`, `Step 2/`, `Step 3/`: initial renaming and commit receipt.
- `reports/STEP4-PERMANENT-REGRESSION-CONSOLIDATION-20261110.md`, `evidence/Step 4/`: legacy-retirement consolidation and commit.
- `reports/STEP5-CUTOVER-REGRESSION-RETIREMENT-20261110.md`, `evidence/Step 5/`: cutover-test retirement and passing regressions.
- `evidence/Step 6/`: cache cleanup, manual renames, failed README-name lookup and successful final run. Superseded command failures are preserved rather than hidden.
- `reports/FINAL-ACCEPTANCE-RECONCILIATION-20261110.md`: accepted implementation evidence and remaining publication/closure criteria.
- `tests/`: preserved original historical Python tests.
- `tools/`: one-off implementation and feature-closure tools, not permanent Playbooks roles.

## Formal closure

Published Playbooks commit `7dfa93fef6d975aa82f5f4cfdf54497b106e7645` was verified against `origin/main` on `mango`. Publication receipt: `evidence/Step 7/playbooks-publication-20261110.txt`. All 0044 evidence was accepted and the entire feature directory moved to `change-control/complete/`. The resulting Diaries commit must be published separately.
