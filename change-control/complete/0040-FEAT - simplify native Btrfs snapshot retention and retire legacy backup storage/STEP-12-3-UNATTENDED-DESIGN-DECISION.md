# 0040-FEAT Step 12.3 — Unattended receiver-pruning redesign

> **SUPERSEDED for Step 12.3 replication/recovery design (5 November 2026).** The current approved direction is [`reports/STEP12-3-SIMPLIFIED-DESIGN-DECISION-20261105.md`](reports/STEP12-3-SIMPLIFIED-DESIGN-DECISION-20261105.md). The material below is preserved as the 29 October historical decision; do not implement its journal/scope/approval machinery as new Step 12.3 requirements. Earlier accepted safety evidence remains valid.

Decision: APPROVED IN PRINCIPLE (2026-10-29). Implementation and production acceptance: OPEN.

## Operating contract

* Native replication, source pruning, receiver pruning and stale-qgroup maintenance are separate unattended operations, coordinated through existing source/receiver locks, received-snapshot receipts, a durable source-parent pin and the receiver deletion journal.
* Both sides must preserve the most recent *verified* common parent required for incremental send/receive; receiver pruning also preserves every newer snapshot. Respect retention policy and additional holds.
* Never infer a protected parent solely from the timestamp of the last successful send. Validate snapshot identities on both hosts, retain the source pin across failures, and do not advance protection until the replacement parent has been verified.
* Receiver deletion must re-check the current protected parent, snapshot identity, retention eligibility, receipt and journal under the manager/writer lock. Interruption/retry must not duplicate an unsafe deletion.
* Do not require individual operator approvals, single-use approval consumption or per-snapshot approval files for routine pruning.
* Pruning should fail closed on missing/unreachable peer, inconsistent ancestry, unresolved recovery or lock conflict. Preserve enough diagnostics for unattended retries and investigation.
* Expose dry-run/plan, structured per-run results, systemd journal logs, last success/failure and qgroup stale counts. Qgroup clean-up must have safe, independently verified lifecycle and idempotency.

## Retirement scope

Remove use of `/etc/btrfs-receiver-prune/`, `/var/lib/btrfs-receiver-prune/consumed/` and the parent directory after confirming they contain no needed forensic/recovery data. Rework source and receiver regression contracts that currently require manual approval. Keep existing receipt storage, source pin, Btrfs identity checks, manager/writer locks, recovery journal and endpoint restrictions.

## Implementation gates

1. Inspect current live configuration and source; freeze affected contract/regression inventory. Production receiver prune remains disabled.
2. Refactor receiver deletion authority from a single-use approval to live, lock-held, retention-authorised validation; cover safe retry and fail-closed cases.
3. Wire separate sender/receiver orchestration without double-acquiring the source lock; confirm unattended scheduler coordination.
4. Run source regressions, then disposable real-Btrfs integration including interrupted send, prune, restart, concurrency and stale-qgroup cleanup.
5. Review Ansible `--check --diff`, controlled deploy on each host, verify runtime operation and idempotency over unattended cycles.
6. Retire approval directories after evidence inspection, archive results, and update change control. Do not declare Step 12.3 closed before gate 6.

## Explicitly deferred

SSH account/privilege separation remains 0041-FEAT; 0040 uses existing `richard` transport and authorised root endpoint. Do not broaden the privileges or expose an unrestricted remote shell.

## Source baseline note

This is a design-decision addendum only, derived from the user's agreed operating model and the 2026-10-26 source archive plus 2026-10-28 regression outputs. It does not claim production configuration or full source is current. No code or Ansible tasks are changed by this ZIP.
