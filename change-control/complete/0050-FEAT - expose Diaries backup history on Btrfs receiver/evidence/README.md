# 0050 execution and acceptance evidence

No feature-specific deployment, host verification or acceptance step has run as part of creating this change-control directory. Store only actual outputs and receipts here, separated by `Step 1/` through `Step 4/` as work progresses. Record UTC timestamps, host/terminal, command, exit code, source/deployed Git revisions, checksums and acceptance decision. The accepted 0049 evidence remains under `change-control/complete/0049-FEAT - rationalise Btrfs and Diaries backup management/` and need not be copied or replayed.

Do not store permanent 0050 evidence in the Playbooks repository, `/home/richard` outside the Diaries checkout, or a remote temporary folder.

## Accepted evidence index — 17 November 2026

- `Step 1/BACKUP-RECEIVED-LAYOUT-20261117.txt` — readonly receiver directory, marker and manifest preflight.
- `Step 2/LOCAL-SOURCE-AND-REGRESSION-20261117.txt` — source and compatibility tests.
- `Step 3/MANGO-0050-SOURCE-AND-CHECK-20261117.txt`, `WINDOWS-0050-FEATURE-TESTS-20261117.txt` — Ansible syntax/check, permanent regressions and receiver-only fixtures.
- `Step 3/MANGO-RECEIVER-DEPLOYMENT-20261117.txt`, `BACKUP-INITIAL-LIVE-ACCEPTANCE-20261117.txt` — initial receiver deployment and diagnosis retained unchanged.
- `Step 3/MANGO-CORRECTED-READER-DEPLOYMENT-20261117.txt`, `BACKUP-FULL-SCHEMA2-VERIFICATION-PASS-20261117.txt` — corrected deployment and full 128-file live verification.
- `Step 3/MANGO-STRICT-IDEMPOTENCE-AND-HISTORY-COMPARISON-20261117.txt`, `FINAL-OPERATIONAL-LOG-SHA256-20261117.md` — strict `changed=0` and 11 receiver-only identities.
- `Step 4/MANGO-PLAYBOOKS-CONTROLLER-FIRST-PUBLICATION-20261117.txt`, `MANGO-PLAYBOOKS-CONTROLLER-MODE-CORRECTION-20261117.txt`, `REPOSITORY-PUBLICATION-LOG-SHA256-20261117.md` — Playbooks/controller publication and executable-bit correction.
- `Step 4/WINDOWS-DIARIES-PUBLICATION-20261117.txt`, `WINDOWS-DIARIES-PUBLICATION-LOG-SHA256-20261117.md` — published Diaries pre-closure evidence commit.

Formal approval is in `reports/FORMAL-CLOSURE-DECISION-20261117.md`. The archive relocation and final remote SHA are established by the guarded closure helper's PASS output, not by this pre-execution index.
