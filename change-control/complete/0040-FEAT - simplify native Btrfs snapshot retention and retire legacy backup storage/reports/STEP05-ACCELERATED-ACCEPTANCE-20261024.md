# 0040-FEAT Step 5 — Accelerated adversarial source regression acceptance

**Decision: CLOSED — 24 October 2026 (accelerated acceptance).**

## Accepted source revision

Playbooks `b51a5b0` (`0040-FEAT: implement snapshot migration and adversarial regressions`), committed on `mango` with clean working tree. Eight source/test files, 262 insertions and 6 deletions; staged diff check passed.

## Observed regression evidence

Executed on `mango` from `/home/richard/playbooks` as root:

`sudo python3 roles/snapshots/tests/verify-0040-step05-suite.py`

The log reports PASS for mixed legacy paired and `@data`-only sets, pin protection, checkpoint holds after dropping required root, root-only incomplete sets blocking prune, disappearing candidate failing before deletion, invalid/duplicate/empty source configuration, required source missing from creation set, receiver ordinary-prune prohibition, and dry-run non-mutation. The included Step 4 migration test and receiver-role guard test passed. The included Step 3 suite passed all eight scripts, including privileged approval/lock binding, interruption, recovery-state classifications, and mocked two-challenge integration. `git diff --check` passed.

## Scope and residual risks

Evidence establishes non-destructive source behaviour, not a real production receiver deletion. Production-shaped cross-host sender-held deletion and replication-failure rehearsals were intentionally **waived by operator** for accelerated completion. No claim is made that those tests ran or that every originally enumerated Step 5 adversarial scenario was independently exercised. In particular, do not infer comprehensive coverage of clock-ordering, duplicate-timestamp, missing-receipt, and real deletion-failure paths beyond the documented existing tests. This is acceptance with explicit test gaps.

Production `mars` still requires `root` and `@data` and still creates both; the `@data`-only cutover has not occurred. `backup` receiver pruning remains disabled. Subsequent Step 6 runtime plans and Step 7+ gates remain OPEN. No live snapshot or legacy deletion is authorised here.

## Evidence provenance

Operator terminal log `note(20261024-215539).txt`: successful Step 5 suite and clean diff check. Operator terminal log `note(20261024-215639).txt`: successful Git commit `b51a5b0` and clean working tree. Runtime logs, if archived, belong in `evidence/Step 05/`, separate from operational source code.
