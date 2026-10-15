# 0035-FEAT Step 8 — Final evidence reconciliation (2026-10-15)

**Disposition: Gate A PASS; Gate B1 PASS; Gate B2 controlled failure evidence PASS within the stated test scope; Step 8 CLOSED by the authorised decisions in `STEP-8-CLOSURE-20261015.md`.** This document records evidence, not approval to prune or alter production schedules.

## Evidence ledger

| Gate / scenario | Evidence | Conclusion and boundary |
|---|---|---|
| Gate A — live inventory | Existing Step 8 Gate A capture and reconciliation; earlier Steps 6–7 | PASS: 52 paired timestamp sets, GFS dry-run keeping 52/52 at capture, checkpoint `20261013-171228Z`, replication pin `20261015-030004Z`, eight accepted receiver receipts with read-only UUID lineage, receiver timers disabled and pluto ext4 safe no-op. These are time-specific, read-only observations. |
| Gate B1 — history | `gate-b1-20261015-100244.txt` | PASS: historic `20261009-154847Z` and current `20261015-003023Z` resolve to actual snapshot-resident/live paths and dataset `production`; current manifest SHA-256 `c64f94a5211a16506838e74686ecd95acd56f56f8e98caff6e14c4a4a9ce4b65`. This is *not* full-data verification or a restore. |
| Gate B2 — offline receiver/retention | Operator execution `note(20261015-100818).txt`; existing Gate B2 documents | PASS: twelve offline assertions on receipt safety, allowed/rejected parents, GFS selection and injected write failure; no kernel or live SSH implied. |
| Gate B2 — real kernel send/receive | Operator execution `note(20261015-101627).txt`; `GATE-B2-KERNEL-ACCEPTANCE-20261015.md` | PASS: five checks covering full and incremental streams, missing parent on independent Btrfs filesystem, truncated full and incremental streams, accepted data preserved. The earlier incorrect same-filesystem missing-parent case is superseded, not counted. |
| Gate B2 — receiver filesystem ENOSPC | `gate-b2-enospc-mango-20261015.txt` | PASS: genuine disposable Btrfs receive exhaustion, failed candidate unaccepted, previous baseline intact and recoverable; distinct from receipt-file exhaustion. |
| Gate B2 — transport/pin/receipt injection | `gate-b2-transport-mango-20261015.txt` | PASS: five simulated fault cases, including independent receipt prerequisite before release of parent pins, and injected receipt publication `ENOSPC`. |
| Gate B2 — actual isolated SSH disconnect | `gate-b2-ssh-disconnect-mango-20261015.txt` (attached) | PASS: actual loopback SSH client interruption before acknowledgement. Does **not** exercise production sender pin lifecycle over that daemon. |
| Gate B2 — actual receipt-publication ENOSPC | `gate-b2-receipt-enospc-mango-20261015.txt` (attached) | PASS: baseline receipt atomically published; genuine disposable Btrfs filesystem pressure prevents new receipt publication; prior receipt intact, new receipt absent, temporary file removed. Does **not** use the production receiver's hardcoded real state directory. |
| Historical schema-2 restore / 0034 | Completed 0034 feature acceptance and Step 11.3/11.4 conclusions as described in 0034 change control | **INHERITED, qualified**: 0034 reports disposable recovery Gates A–D for current backup ID `20261015-003023Z` and source snapshot `20261015-030004Z`; the underlying original Gate A–D transcripts were not available in inspected sources. No new 0035 full restore, `diaries-backup-history verify` data hashing or DB/application consistency run is represented here. |
| Quantitative Btrfs transport and allocation | No suitable measured `btrfs send` byte counts, receiver allocation before/after, or throughput transcript in inspected acceptance inputs | **NOT VERIFIED**. Counts of snapshots, receipts, or logical backup IDs are not replacements for physical allocation/stream bytes. |

## Verbatim new operator evidence

- `gate-b2-ssh-disconnect-mango-20261015.txt`: actual loopback SSH disconnect PASS; production sender lifecycle not covered.
- `gate-b2-receipt-enospc-mango-20261015.txt`: baseline receipt, genuine publication ENOSPC, previous receipt preservation and cleanup PASS.

These transcripts are copied unchanged from operator uploads and are the authoritative observable results for those two tests. The supplied ZIP contains no Playbooks source changes.

## Final Step 8 acceptance decisions — resolved on 2026-10-15

The following earlier questions are retained as the historical pre-closure decision record; their final dispositions are authoritative in `STEP-8-CLOSURE-20261015.md`.

## Remaining Step 8 acceptance decisions

1. **Schema-2 restore:** explicitly accept the inherited 0034 closure and identify its original Gates A–D transcripts if obtainable; or run a new isolated schema-2 restore using `20261015-003023Z` from a real snapshot path, capturing DB and file validation. Do not imply missing primary evidence was examined.
2. **Transport efficiency:** capture non-destructively from existing transfer journal/logs, if available, native full and incremental bytes plus `btrfs filesystem usage` / quota-safe before/after allocation. If unavailable, obtain explicit written risk/measurement deferral; do not invent figures or run production replication merely to generate measurements.
3. **Gate B2 integration scope:** acknowledge that real SSH disruption, receipt publication ENOSPC, sender pin lifecycle and Btrfs receive recovery were tested in complementary isolated harnesses, not one combined production-equivalent test. Accept or require a wholly disposable combined exercise.
4. **Retention:** GFS policy bucket selection is covered by offline assertions and existing live dry-run. Actual destructive prune across multiple GFS buckets was not performed on production; retain this boundary unless separately authorised.

**Final disposition:** Step 8 CLOSED per `STEP-8-CLOSURE-20261015.md`. This supersedes the preceding provisional recommendation. Feature-wide closure and production schedule/prune changes are not authorised by this Step 8 decision.
