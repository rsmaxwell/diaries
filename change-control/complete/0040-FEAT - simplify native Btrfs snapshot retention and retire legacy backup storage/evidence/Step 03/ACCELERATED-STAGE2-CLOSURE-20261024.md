# 0040-FEAT Step 3 — Accelerated Stage 2 acceptance (24 October 2026)

**Decision: Stage 2 ACCEPTED with explicit operator risk waiver.** This is a non-destructive integration acceptance, not live cross-host deletion approval.

## Current operator evidence

- Playbooks `8d3e66d` (`HEAD -> main`, `origin/main`), clean `git status --short`.
- `sudo python3 roles/btrfs-replication/tests/verify-step03-coordination-suite.py` on `mango`: **all eight scripts PASS**. In particular, root-required lock-bound approval and two fresh challenges/journal-backed mocked completion now PASS (earlier unprivileged run skipped the positive integration fixture).
- Competing approval consumption (eight attempts), replay, permissions/expiry, source timeout/pin, disconnect/stall, journal classification and fail-closed recovery fixtures PASS.
- Python `compileall` passed in the preceding unprivileged run.
- Live `backup` receiver recovery returned `CLEAN`, `authorizes_repair=false`; installed config `mode=receiver`, `receiver_prune_enabled=false`.
- `mars` and `backup` Btrfs filesystem/snapshot-area prechecks passed; previous Step 3 disposable real-Btrfs local transaction/recovery evidence accepted. No additional production deletion performed.
- Earlier recorded Ansible deployment, installed-source parity and second real run `changed=0` remain the accepted deployment/idempotency evidence.

## Evidence provenance

Operator logs: `note(20261024-201330).txt` (filesystem/journal/status); `note(20261024-201446).txt` (source interfaces/revision); `note(20261024-201728).txt` (unprivileged regression, recovery and disabled prune); `note(20261024-201917).txt` (full root-required suite PASS). The logs were reviewed in the session and are *not* included in this ZIP.

## Accepted limitation and ongoing guardrails

At operator request for accelerated completion, the genuine `mars`-originated disposable-snapshot → isolated `backup` receiver transaction, with interruption across both hosts, **was not executed**. Mocked two-challenge completion and earlier *local* real-Btrfs deletion do not establish an end-to-end cross-host deletion test. This gap is consciously accepted as residual risk for the **design/Stage 2 gate**, not as a proof of production-ready receiver pruning.

No existing production snapshots, source holds, checkpoint holds, replication receipts or receiver state may be deleted under this acceptance. Production pruning stays disabled, and actual activation retains the Step 9/12 safeguards and explicit approval. Legacy removal remains dependent on Step 10 identity-specific review and Step 11 separate authorisation.

## Gate outcome

**Stage 2 CLOSED (risk accepted).** Proceed to Step 3 final design/acceptance review. No new runtime deployment or destructive rehearsal is required merely to record this acceptance.
