# 0040-FEAT — Sender-side protected plan integrity

Status: **Locally tested; awaiting mango regression and controlled Ansible review**.

## Scope

The already-deployed non-destructive `--protected-prune-plan` operation now fails closed on duplicate or malformed candidate timestamps, candidates that are not strictly older than the protected common parent, contradictory count totals, invalid identity/safety claims, and non-integral counts. It retains the existing source pruning pin on any failure. There is no deletion entrypoint and no change to the existing `--latest` send path.

## Local verification

- `protected-plan-integrity.py`: 10 tests passed.
- Existing `protected-retention-sender.py`: 5 tests passed.
- Python compile: passed.

## Boundaries and outstanding prerequisites

- Source-level simulation only; mango and deployed behavior have not been verified.
- A reported candidate is **not** deletion authority. The receiver must independently re-verify each candidate, receiver and source identities, explicit preservation of historical checkpoints, retention buckets, locks, durable receipts and recovery state immediately before deletion.
- There is no safe production deletion CLI or sudoers delegation. Receiver pruning stays disabled.
- Current production receiver plan has 19 snapshots retained and 0 candidates; do not adjust retention to create test candidates.
- The current source protection pin must be preserved until a separately validated release/reconciliation workflow exists.

## Change-control

Feature remains OPEN. Do not claim the trusted deletion executor is integrated, deployed or tested by this package.
