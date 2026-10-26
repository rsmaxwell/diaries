# 0040-FEAT — Step 12.1–12.2 source verification evidence

**Date:** 26 October 2026  
**Status:** source verification PASSED; Step 12 overall OPEN; deployment NOT authorised.

## Scope and implementation

Step 12.1 — `roles/btrfs-replication/files/btrfs-native-push-receiver.py`: `protected_retention_candidates()` retains the verified protected parent and every newer received timestamp in addition to existing retention policy; no deletion authority is granted. New regression: `roles/btrfs-replication/tests/verify-0040-step12-parent-boundary.py`.

Step 12.2 — `roles/snapshots/files/btrfs-snapshot-manager.py`: internal `receiver_delete_one_locked()` rejects `stamp >= protected_stamp` before inventory, journal or callback. New regression: `roles/snapshots/tests/verify-0040-step12-2-delete-boundary.py`.

The two source edits were made in `/home/richard/playbooks` on `mango`, which already contained extensive unrelated uncommitted 0040 migration changes. Do **not** treat the entire `git diff` in the raw log as changes made for Step 12.2. Recorded Playbooks revision before implementation: branch `main`, HEAD `a8f857c3b4f2ff57dd83d58bbbe0a99150797625` (19:09 log); this is NOT a clean-tree or post-implementation commit claim. No Git commit is evidenced for these new edits.

## Observed test results

- 19:18: Installed receiver-manager boundary test ran on `backup`, initiated via SSH from `mango`: PASS. It rejected deliberately invalid identities before callbacks; manager/writer locks distinct, required holds configured, pending journal absent, pruning disabled. It did not test live deletion.
- 19:29: Step 12.1 parent-selection regression PASS; Python `py_compile` and `git diff --check` completed successfully.
- 19:44: Six source compatibility regressions PASS (approval contract/consumption/lock binding/recovery/prune approval/new parent boundary); Python syntax and whitespace checks PASS.
- 21:50: Step 12.2 adversarial regression PASS: parent and newer candidate fail before inventory, journal and callbacks; malformed identities fail closed; older candidate reaches next gate; guarded production prune stays blocked. `py_compile` and `git diff --check` completed successfully.
- 21:51: Six relevant compatibility regressions PASS (receiver recovery states, lock binding, prune approval, approval consumption, Step 12.1 and Step 12.2); syntax and `git diff --check` PASS.

**Limitations:** Regression tests are predominantly source-only/mocked. They do not exercise a live source-held lease, competing sender/receiver locks, verified real Btrfs deletion, interrupted cross-host coordination or production authorisation. Production `receiver_prune_enabled=false` remains required. No source deployment, Ansible check/diff, runtime idempotency or live pruning has been accepted for Step 12. The Stage 12.1–12.2 source verification is accepted **only** as a prerequisite for the next stage.

## Remaining gates

1. Step 12.3: design and adversarially test source pin lifetime, receiver writer/manager lock ordering, parent UUID binding, interruption and stale-approval handling; fail closed on any uncertainty.
2. Disposable real-Btrfs test and integration verification before any live enablement.
3. Ansible `--check --diff`, controlled deployment authorisation, rollback, runtime and idempotency evidence.
4. Reconcile archived source revision and commits before formally closing Step 12.

## Archived raw operator logs

The files below are copied verbatim from uploaded operator logs; the table supplies SHA-256 so they can be checked after application.

| Raw log | SHA-256 |
|---|---|
| `raw-logs/note(20261026-190917).txt` | `7439cc1ea89551281d36b6955c1274193698ed68c6295962d35d4eda42eadd08` |
| `raw-logs/note(20261026-191829).txt` | `7c0609ef0ce851e89a3a854df428cb38450d634a4319922a2dc457b657769408` |
| `raw-logs/note(20261026-192912).txt` | `3720dd25c088e0e5def43fadc52f898ee192b602353eda06c162b86dc79bb580` |
| `raw-logs/note(20261026-194448).txt` | `9294a6909a8b0c5a90b29afc0d485e64c17338a661b7ba99ffb8d38c9b6bbf14` |
| `raw-logs/note(20261026-215044).txt` | `71f5e40fa3e88c4856ed2a22112461e920e8a77560ea88e39231a6ab3b571c53` |
| `raw-logs/note(20261026-215156).txt` | `683982c4ec97518cce03583e57d81548ca2fa462a357561052955381133acaf0` |

The earlier 19:09 baseline test failure was caused by running a backup-host-specific installed-manager test on `mango`; the correct remote execution passed at 19:18.
