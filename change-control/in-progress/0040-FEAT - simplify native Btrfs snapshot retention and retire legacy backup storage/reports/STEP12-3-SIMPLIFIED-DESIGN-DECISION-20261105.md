# 0040-FEAT — Simplified agreed-parent replication and next-run retry

**Decision date:** 5 November 2026. **Status:** APPROVED DESIGN DIRECTION; implementation and production acceptance OPEN.

This is the **current Step 12 design**, superseding the proposed two-phase transactional/journal/scoped/staged-receive design in the October/early-November Step 12.3 reports and prototypes. Earlier reports, accepted manual A→B evidence and original feature closure decisions remain historical evidence, not instructions for the new implementation.

## Objective and accepted trade-off

Maintain native incremental Btrfs replication from `mars` to `backup`, with a verified **common agreed parent** protected from pruning on both hosts. The **next scheduled replication run automatically recovers an ordinary interrupted receive and retries**. If retries repeatedly fail or recovery is ambiguous, log a useful error and leave resolution to the operator. Prioritise simple operation over elaborate crash-transaction machinery; the operator explicitly accepts the additional residual risk.

## Components (minimal, source-controlled)

1. **One tiny agreed-parent state file on each host**. At minimum record the established timestamp and source subvolume UUID (or enough immutable identity to validate the corresponding received UUID). Write via atomic replacement; it is **not** a per-transfer journal. Update receiver first, source second after verifying transfer. Old format/receipts remain intact until the replacement has been tested and accepted.
2. **One sender-initiated native transport**: ordinary `btrfs send -p <common-parent> <candidate>` over SSH into ordinary `btrfs receive <receiver-directory>`. No stream rewriting, staging-name protocol, transactional publication witnesses, receiver scope systemd units, proof-key transaction protocol or multi-phase promotion/acknowledgement.
3. **One non-blocking local lock on each host**, shared by operations that could change/inspect that host's snapshot or parent state: receive, replication coordination and pruning (and snapshot creation where necessary). Exit/defer on contention; the receiver process must retain its lock for the full `btrfs receive` lifetime. Locks are local, not a distributed transaction protocol.
4. **Ordinary logs and systemd status**: time, parent/candidate, UUIDs, transferred/verified/deferred/retried/failed result and reason; no durable per-stage journal. The state file is the only new persistent replication decision state. Existing historic receipts/holds remain available for rollback until review.
5. **One shared retention selector** installed on `mars` and `backup`. Under its local lock, it never prunes the locally recorded agreed parent or independent protected checkpoints/holds. An incomplete candidate is never eligible for retention selection as a valid received snapshot. No duplicate receiver pruning authority.

## Normal scheduled cycle

1. Sender obtains its **non-blocking** host lock; if busy, log `DEFERRED` and stop. Ask receiver to perform its checks/receive under the **receiver's** non-blocking host lock. Do not run two sends concurrently.
2. Compare both agreed-parent records and Btrfs snapshot identities. If they agree, choose one next eligible read-only candidate. If state differs by one known fully verified transfer, reconcile from actual immutable Btrfs identity; otherwise stop and log a conflict. Never guess a parent by filename alone.
3. If receiver already has the candidate **fully received, read-only, with correct Received UUID**, treat the transfer as complete, including a lost acknowledgement. Otherwise handle an interrupted partial candidate as below.
4. Run native incremental send/receive, with bounded timeout and correct pipeline/SSH exit-status handling. Verify receiver candidate identity, read-only status and expected Received UUID. Do not advance the parent on failure.
5. Update the receiver's small agreed-parent file **first**, then the sender's, with independent readback. Recheck both. On the next invocation, reconcile a verified one-sided update without retransmitting. Keep/prune the old parent only once the local host can verify common-parent convergence; if uncertain, preserve both old and new until reconciliation.
6. Log `SUCCESS` or a clear `DEFERRED`/`FAILED` reason. The next scheduled run handles incomplete work; no aggressive immediate retry loop.

## Interrupted receive and next-schedule retry

- If the candidate is absent, send it normally.
- If it is a **verified complete received snapshot**, do **not** delete or retransmit; reconcile state and proceed.
- If the candidate is a clearly **incomplete** receive created at the exact expected timestamp in the dedicated receiver-only tree, under the host lock, and Btrfs inspection confirms it is **not** a valid read-only received snapshot, protected parent, held checkpoint or other known valid object: perform a *targeted* `btrfs subvolume delete`, verify absence, then retry the candidate **once in that scheduled invocation**. Never use recursive `rm -rf` as a Btrfs subvolume substitute.
- If the object is a symlink, has the wrong UUID/type, is protected, has conflicting read-only/received metadata, or the receive process may still be running, **do not delete or retry**. Log for manual review. Non-blocking lock ownership should make overlap unlikely, but locks must remain held by the actual receive child.
- Network/SSH/busy-lock/timeout failures preserve agreed-parent state and are retried at the next schedule. A second failed invocation generates another log/error; after persistent failures the operator investigates and corrects the underlying issue manually. No new permanent retry-state machine is required.

## Pruning and scheduling

Keep existing operational schedules unless separately changed under deployment review: native sender push currently **03:30 UTC**, snapshot creation **08:00 UTC**, source prune **08:15 UTC**, and source pull **01:45 UTC**. Confirm receiver prune schedule before activation and offset it from sending/other writes. Different times make clashes rare; non-blocking locks handle exceptions. Retention remains **48 hourly, 14 daily, 12 weekly, 24 monthly and 5 yearly**; existing historical holds and source/receiver parent protection survive. Receiver pruning activation remains separately gated under original Step 12.

## Intentionally removed from the target design

Per-transfer durable transaction journal, pending/previous state machine and explicit previous-parent acknowledgement; custom Btrfs send-stream transformation; private staging names; publication witnesses and atomic staging publication; systemd scoped receive supervision; process-identity/ownership witness tracking; cryptographic per-transfer completion proofs; multi-step receiver promotion and separate sender-retry permission tokens. These are *retired design proposals*, not evidence that currently installed files or services have been removed.

## Acceptance and rollback

- Source tests: normal advancement; identical/one-step divergent state; lost acknowledgement without retransmit; lock contention/back-off; protected parent in both pruners; valid snapshot not deleted; incomplete snapshot cleaned only under receiver lock; repeated failure diagnosed; malformed/ambiguous state refusal.
- One **disposable real-Btrfs** interrupted-receive followed by next-invocation cleanup/retry; no need to repeat the previously accepted A→B production transfer or full restore.
- Check actual installed commands and Git state on `mango`, `mars`, and `backup`; review Ansible `--check --diff`, run one controlled normal cycle and one interrupted/retry cycle, check UUIDs, file contents, parent holds, locks, timers and logs. Record resulting raw evidence and rollback state in the Diaries feature directory.
- **No automatic pruning of established parents or deletion of ambiguous candidates.** Existing 03:30 native job and its rollback remain in place until a tested cutover is accepted. Step 12.3 and Step 12 remain **OPEN** until this evidence and operator acceptance are recorded.

## Verification/test cleanup

Source prototypes and tests for the superseded Step 12.3 architecture may be retired from the permanent Playbooks role **after preserving their exact bytes and checksums** under this feature's `tests/retired-step12-3/` directory. The provided dry-run-first cleanup tool archives eligible historical test scripts and removes only those scripts, not production modules, Ansible tasks or already accepted evidence. Retain general native Btrfs, shared-retention and pruning tests; replace removed prototype coverage with a compact simplified regression suite. Clean the obsolete production modules only as part of the reviewed deployment/change package, never by treating test deletion as runtime removal.
