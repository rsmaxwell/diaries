# 0040-FEAT Step 12.3 — Durable agreed-parent redesign (design proposal)

Date: 2026-10-30. Status: DESIGN / NOT DEPLOYED. This report is additive; the live Playbooks source has evolved since the 2026-10-26 source archive.

## Decision

The sender (`mars`) initiates Btrfs send/receive. Both endpoints maintain durable, UUID-bound records identifying the common replication parent. After each successfully received and verified snapshot, the parent advances; sender and receiver prune their own histories locally, but must preserve the agreed parent and any in-flight transfer parent. No sender challenge/response is needed for each receiver prune.

## Evidence and baseline

- The Oct 26 source selects the most recent verified common parent by comparing sender subvolume identities with receiver receipts (`choose_parent`); source `protect-source` pins parent and candidate, and releases the former only after a verified receiver receipt. This is not a single durable agreed-parent record on both endpoints.
- Oct 30 live evidence: temporary receiver retention 24 hourly yielded candidate `20261012-100003Z`; one receiver-only delete removed its subvolume and receipt, leaving 25 complete snapshots and no pending journal, but sender reported `Untrusted transaction completion`. One stale qgroup then appeared. Source protection pins persisted.
- The rollback `--check --diff` showed exactly two config changes restoring 24 to 48 hourly. Successful application and idempotency evidence are NOT YET PROVIDED.

## Safety invariants

1. Parent identities comprise a timestamp, source UUID, filesystem UUID and verified receiver receipt. A matching name alone is insufficient.
2. At every durable boundary, at least one common, valid parent is preserved at both ends; never release the previous parent before durable new-parent acceptance is established at both ends.
3. On uncertain acknowledgement, disagreement or interrupted transition, keep both old and new parents (as applicable) and fail closed for pruning. Never infer a committed transition solely from a successful `btrfs receive` exit.
4. Local snapshot pruning and replication on each host use compatible locks; receiver deletes cannot race an active receive or parent transition. Parent pins are exempt from retention irrespective of age.
5. Preserve historical receiver holds `20261013-171228Z` and `20261018-165453Z`, receipts, journal recovery and conservative handling of stale qgroups.
6. Retention remains 48/14/12/24/5 (hourly/daily/weekly/monthly/yearly), with 30-minute minimum age unless a separately reviewed test override is active.
7. No automatic deletion without explicit new acceptance evidence. Missing or contradictory state never authorises pruning.

## Proposed transition protocol (requires code review)

- PREPARE: sender locks local replication, verifies current agreed parent, pins current and candidate, and advertises transition ID, old and new UUIDs; receiver locks receive/writer and persists a PREPARED transition with old parent still pinned.
- RECEIVE: transfer candidate via Btrfs incremental send; receiver validates readonly identity and receipt, writes and fsyncs an ACCEPTED record while retaining both pins.
- COMMIT: sender observes the accepted receipt and durably writes its new-parent record; receiver can finalize its parent only after a safe durable coordination rule is specified. Loss of acknowledgement must preserve old+new, then reconcile before pruning either.
- RECONCILE: compare immutable receipts and recorded transition IDs after crash/reconnect. Resolve mismatches conservatively; fall back to full reseed only by explicit operator action.
- PRUNE: sender and receiver independently compute retention against their own locked local inventories, subtract pinned parent(s) and holds, journal receiver deletes, and record completion locally. No interactive sender challenge per deletion.

**Distributed-safety note:** two independent writes cannot be atomic. A naive 'receiver updates to B then sender updates to B' permits receiver to delete A before the sender commits. The implementation must explicitly preserve A across this window, using a two-phase/acknowledged transition or equivalent recoverable fencing. Merely storing 'latest = B' separately on both hosts is insufficient.

## Required regression gates

- Successful A→B and next B→C incremental transfer; old pin retired only after durable convergence.
- Crash at each commit/write/acknowledgement point; old and new parent preserved until reconciliation.
- Receiver accepted B but sender still records A; receiver prune refuses A.
- Sender records B but receiver still records A; source prune refuses A.
- Concurrent receiver prune and receive, missing/altered receipt, forged UUID, stale or missing pin, duplicate messages, interrupted journal.
- Receiver-only prune removes one eligible historical candidate while source/receiver parent(s) and historical holds survive.
- Full restore rehearsal on disposable Btrfs data; never use production for first failure-mode exercises.

## Deployment sequence / open gate

1. FIRST: restore receiver retention to 48 hourly using normal Playbooks run on `backup` (no `--extra-vars`), then repeat for idempotency and verify both JSON policies and `receiver_prune_enabled=false`. Preserve logs.
2. Capture current post-delete source + receiver configuration/state and Git diff from `mango`; reconcile against this report, since Oct 26 ZIP predates live Stage B.
3. Implement prototype and tests in feature directories. Keep unattended pruning disabled.
4. Regressions → Ansible `--check --diff` → controlled rollout to `mars` and `backup` in separately verified gates → runtime/idempotency → archive evidence.

This design is not a production instruction and does not authorise snapshot deletion.
