# 0036-FEAT Step 8 — Gate D unattended acceptance and formal closure (2026-10-18)

**Disposition: Gate D CLOSED — PASS (2026-10-18).** Two distinct, genuinely unattended daily production cycles completed successfully on 17 and 18 October 2026. Acceptance is based on actual scheduled host journal evidence, fixed-dataset manifest/eligibility metadata, Btrfs snapshot journal and off-site receiver receipts, independently reconciled. **Gate E remains OPEN; Step 8 and 0036-FEAT remain IN PROGRESS.**

## Evidence and custody

- Operator-collected `0036-gate-d-evidence-cycle-1.tar.gz` (17 October, previously reviewed and accepted).
- Operator-collected `0036-gate-d-evidence-cycle-2.tar.gz` (18 October; collected `2026-10-18T07:28:10Z` with `verification/0036-gate-d/collect-gate-d.sh` on `mango`). Preserve the original evidence archives separately; this documentation patch deliberately does not embed or modify runtime evidence.
- Cycle 2 archive sections: `collection.txt`, `pluto-timer.txt`, `pluto-capture-journal.txt`, `pluto-capture-current.txt`, `mars-timers.txt`, `mars-pull-journal.txt`, `mars-pull-current.txt`, `mars-snapshot-journal.txt`, `mars-snapshots.txt`, `mars-push-journal.txt`, `backup-receipts.txt`, `backup-latest-receipt.txt`.
- Collector succeeded in all eleven categories, all four journal classes `status=ENTRIES`; independently read and correlated content instead of treating collection exit status as acceptance.

## Accepted unattended cycles

| Evidence | Cycle 1 — 2026-10-17 | Cycle 2 — 2026-10-18 |
| --- | --- | --- |
| `pluto` scheduled fixed schema-2 capture | PASS; backup `20261017-003102Z` | PASS; backup `20261018-003102Z`; completed `00:31:12Z` |
| Logical dataset / durable Files | `production` / 89 | `production` / 89; 100,032,776 bytes |
| Fixed receive on `mars` | `VERIFIED_FIXED_RECEIVE` at ~01:30Z | `VERIFIED_FIXED_RECEIVE` at `01:30:16Z` |
| Source/receiver manifest SHA-256 | `51ce67b1c5a7e222b9ac9e431bb81e07885c0743aa8ff63082fbaf7917cdb6a4` | `a4a38d6491d038af2fe6e2b98e5fcb006c8f39d084fe68bd7c365f90eac2baab` |
| Verified snapshot on `mars` | `20261017-030007Z` | `20261018-030006Z`, verified `03:00:37Z` |
| Off-site transfer | Accepted Btrfs incremental | Accepted Btrfs incremental; finished ~03:31Z |
| Incremental parent | `20261016-030037Z` | `20261017-030007Z` |
| Receiver receipt | Accepted `20261017-030007Z` | Accepted `20261018-030006Z`; `completed_at_utc=2026-10-18T03:31:20.939823+00:00` |
| Off-site consistency | Source/received UUID match; read-only | source UUID = received UUID `f91b322a-4aa7-ad45-a766-d7a1e2eb15b9`; `read_only_verified=true`; send/receive exit `0`/`0` |
| Result | **PASS** | **PASS** |

Cycle 2 source manifest, source verification marker, `mars` dataset manifest and receiver eligibility marker all carry backup `20261018-003102Z` and manifest hash `a4a38d6491d038af2fe6e2b98e5fcb006c8f39d084fe68bd7c365f90eac2baab`. Receiver marker has `snapshotEligible=True`, verification time `2026-10-18T01:30:15.959042Z`, and destination relative path `backup/pluto/diaries-backup`. Snapshot log records `VERIFIED-DIARIES production 20261018-003102Z` before creating the paired read-only timestamp set. Native push log records incremental parent `20261017-030007Z`, `ACCEPTED` for new snapshot, and successful service completion; receiver receipt independently records destination `/@data/mars-received/@data/20261018-030006Z` and matching UUID.

Observed production schedules: fixed capture 00:30 UTC, guarded pull 01:30 UTC, hourly Btrfs create at :00 and prune at :15, and off-site push 03:30 UTC. Scheduled services finished successfully and timers remained active/enabled at the evidence collection point. No manual service triggering was needed for either accepted daily cycle.

## Acceptance boundary and decision

**Gate D acceptance criteria satisfied.** Two separate unattended end-to-end cycles demonstrate coherent logical capture, guarded fixed reception, snapshot eligibility, 0035 read-only snapshot creation and 0034 off-site incremental lineage/receipt. Previously accepted Step 7 restored-data correctness evidence is inherited; no repeat full restore is required. Quantitative transfer/allocation measurements and savings thresholds are explicitly excluded by operator agreement. This review does not claim a fresh full restore or new direct manifest validation inside the remote received snapshot; those are not Gate D requirements.

**Gate E is not authorised by this closure alone.** Keep `pluto` and `mars` fixed-mode operational schedules active; retain `.pre-0036-rollback` symlinks, original generation trees, historical snapshots, off-site receipts, replication protection/checkpoint holds and prior configurations. Do not decommission anything or delete old generations without Gate E review and separate explicit deletion approval. No application Docker image rebuild is required.

**Formal decision (2026-10-18): Gate D CLOSED — PASS. Gate E OPEN. Step 8 OPEN. 0036-FEAT OPEN.**
